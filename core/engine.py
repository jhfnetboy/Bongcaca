from faster_whisper import WhisperModel
import os
import logging
from huggingface_hub import snapshot_download
import psutil
from utils.config import Config
import sys
import tempfile
import numpy as np
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
import time
import wave
import threading

# 设置环境变量以避免OpenMP冲突
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

logger = logging.getLogger(__name__)

class WhisperEngine:
    def __init__(self, config: Config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.model = None
        self.model_name = None
        self.settings = None
        self.initialized = False
        self.buffer = []  # 用于实时转写的音频数据缓冲区
        self.buffer_size = 0  # 当前缓冲区大小(字节)
        self.available_models = self._detect_models()
        self.max_buffer_size = 1024 * 1024 * 10  # 限制缓冲区大小为10MB
        
        # 性能优化：添加模型加载状态跟踪
        self._model_loading = False
        self._model_load_lock = threading.Lock()
        self._last_model_access = 0
        
    def _detect_models(self) -> List[Dict[str, Any]]:
        """检测已下载的模型，返回可用模型列表"""
        self.logger.info("Detecting downloaded models...")
        available_models = []
        
        # 检查模型是否已下载
        model_checks = [
            ("large-v3", os.path.expanduser("~/.cache/huggingface/hub/models--Systran--faster-whisper-large-v3")),
            ("medium", os.path.expanduser("~/.cache/huggingface/hub/models--Systran--faster-whisper-medium")),
            ("small", os.path.expanduser("~/.cache/huggingface/hub/models--Systran--faster-whisper-small")),
            ("base", os.path.expanduser("~/.cache/huggingface/hub/models--Systran--faster-whisper-base")),
            ("tiny", os.path.expanduser("~/.cache/huggingface/hub/models--Systran--faster-whisper-tiny")),
            ("distil-large-v3", os.path.expanduser("~/.cache/huggingface/hub/models--Systran--faster-distil-whisper-large-v3")),
            ("distil-small.en", os.path.expanduser("~/.cache/huggingface/hub/models--Systran--faster-distil-whisper-small.en")),
            ("distil-medium.en", os.path.expanduser("~/.cache/huggingface/hub/models--Systran--faster-distil-whisper-medium.en"))
        ]
        
        for model_name, model_path in model_checks:
            if os.path.exists(model_path):
                self.logger.info(f"Found {model_name} model at: {model_path}")
                available_models.append({
                    "name": model_name,
                    "path": model_path,
                    "compute_type": "int8",
                    "device": "cpu",
                    "threads": self._get_optimal_threads_for_model(model_name)
                })
                
        if not available_models:
            self.logger.warning("No downloaded models found")
            
        return available_models
    
    def _get_optimal_threads_for_model(self, model_name: str) -> int:
        """根据模型和系统资源，返回最优的线程数"""
        cpu_count = psutil.cpu_count(logical=False)
        if cpu_count is None:
            cpu_count = psutil.cpu_count(logical=True)
            if cpu_count is None:
                cpu_count = 2
        
        if model_name == "large-v3" or model_name == "distil-large-v3":
            return min(cpu_count, 8)  # 使用最多8个线程
        elif model_name == "medium" or model_name == "distil-medium.en":
            return min(cpu_count, 6)  # 使用最多6个线程
        elif model_name == "small" or model_name == "distil-small.en":
            return min(cpu_count, 4)  # 使用最多4个线程
        else:  # base, tiny or other
            return min(cpu_count, 2)  # 使用最多2个线程
        
    def get_optimal_settings(self) -> Dict[str, Any]:
        """根据系统资源情况，优化配置参数"""
        # 检查系统内存和CPU
        system_ram = psutil.virtual_memory().total / (1024 ** 3)  # GB
        cpu_count = psutil.cpu_count(logical=False)
        if cpu_count is None:
            cpu_count = psutil.cpu_count(logical=True)
            if cpu_count is None:
                cpu_count = 2
                
        # 首先检查是否有可用的已下载模型
        if self.available_models:
            # 优先使用large-v3
            for model_info in self.available_models:
                if model_info["name"] == "large-v3":
                    self.logger.info(f"Using pre-downloaded large-v3 model")
                    return {
                        "model_name": "large-v3",
                        "device": "cpu",
                        "compute_type": "int8",
                        "beam_size": 5,
                        "threads": model_info["threads"]
                    }
            
            # 如果没有large-v3，但有medium
            for model_info in self.available_models:
                if model_info["name"] == "medium":
                    self.logger.info(f"Using pre-downloaded medium model")
                    return {
                        "model_name": "medium",
                        "device": "cpu",
                        "compute_type": "int8",
                        "beam_size": 5,
                        "threads": model_info["threads"]
                    }
            
            # 如果没有medium，但有small
            for model_info in self.available_models:
                if model_info["name"] == "small":
                    self.logger.info(f"Using pre-downloaded small model")
                    return {
                        "model_name": "small",
                        "device": "cpu",
                        "compute_type": "int8",
                        "beam_size": 5,
                        "threads": model_info["threads"]
                    }
            
            # 使用任何已下载的模型
            model_info = self.available_models[0]
            self.logger.info(f"Using pre-downloaded {model_info['name']} model")
            return {
                "model_name": model_info["name"],
                "device": "cpu",
                "compute_type": "int8",
                "beam_size": 5,
                "threads": model_info["threads"]
            }
        
        # 如果没有已下载的模型，根据系统资源选择
        self.logger.info("No downloaded models found, selecting based on system resources")
        # 检查是否已下载大模型
        large_model_path = os.path.expanduser("~/.cache/huggingface/hub/models--Systran--faster-whisper-large-v3")
        if os.path.exists(large_model_path):
            self.logger.info(f"Found large-v3 model at: {large_model_path}")
            model_name = "large-v3"
            compute_type = "int8"
            beam_size = 5
            # 对于多核CPU，使用更多线程
            threads = min(cpu_count, 8)  # 使用最多8个线程，避免过度使用
        # 如果系统内存>=16GB且CPU核心数>=8，使用medium模型
        elif system_ram >= 16 and cpu_count >= 8:
            self.logger.info(f"System has {system_ram:.1f} GB RAM and {cpu_count} CPU cores. Using medium model.")
            model_name = "medium"
            compute_type = "int8"
            beam_size = 5
            threads = min(cpu_count, 6)  # 使用最多6个线程
        # 如果系统内存>=8GB且CPU核心数>=4，使用small模型
        elif system_ram >= 8 and cpu_count >= 4:
            self.logger.info(f"System has {system_ram:.1f} GB RAM and {cpu_count} CPU cores. Using small model.")
            model_name = "small"
            compute_type = "int8"
            beam_size = 5
            threads = min(cpu_count, 4)  # 使用最多4个线程
        # 否则使用tiny模型
        else:
            self.logger.info(f"System has {system_ram:.1f} GB RAM and {cpu_count} CPU cores. Using tiny model.")
            model_name = "tiny"
            compute_type = "int8"
            beam_size = 3
            threads = min(cpu_count, 2)  # 使用最多2个线程
            
        self.logger.info(f"Using {model_name} model with {threads} threads")
        
        # 确定是否使用GPU
        device = "cpu"  # 默认使用CPU
        
        # 如果有足够内存的NVIDIA GPU，可以考虑使用cuda
        # TODO: 检测GPU并自动配置
        
        return {
            "model_name": model_name,
            "device": device,
            "compute_type": compute_type,
            "beam_size": beam_size,
            "threads": threads
        }
        
    def _has_gpu(self):
        """检查是否有可用的GPU"""
        try:
            import torch
            return torch.cuda.is_available()
        except:
            return False
            
    def ensure_model_loaded(self):
        """确保模型已加载 - 优化版本，线程安全且智能缓存"""
        if self.model is not None:
            self._last_model_access = time.time()
            return
            
        # 使用锁确保线程安全的模型加载
        with self._model_load_lock:
            # 双重检查锁定模式
            if self.model is not None:
                self._last_model_access = time.time()
                return
                
            if self._model_loading:
                # 如果模型正在加载，等待加载完成
                while self._model_loading and self.model is None:
                    time.sleep(0.1)
                if self.model is not None:
                    self._last_model_access = time.time()
                    return
                    
            self._model_loading = True
            
            try:
                # 获取设置
                if not self.settings:
                    self.settings = self.get_optimal_settings()
                
                model_name = self.settings["model_name"]
                compute_type = self.settings["compute_type"]
                device = self.settings["device"]
                cpu_threads = self.settings["threads"]
                
                # 性能优化：设置环境变量
                os.environ["OMP_NUM_THREADS"] = str(cpu_threads)
                os.environ["MKL_NUM_THREADS"] = str(cpu_threads)
                
                self.logger.info(f"Loading model {model_name} with {cpu_threads} threads...")
                start_time = time.time()
                
                # 加载模型
                self.model = WhisperModel(
                    model_name,
                    device=device,
                    compute_type=compute_type,
                    cpu_threads=cpu_threads,
                    download_root=self.config.models_dir
                )
                
                load_time = time.time() - start_time
                self.model_name = model_name
                self.initialized = True
                self._last_model_access = time.time()
                
                self.logger.info(f"Model {model_name} loaded successfully in {load_time:.2f}s")
                
            except Exception as e:
                self.logger.error(f"加载模型时出错: {str(e)}")
                raise
            finally:
                self._model_loading = False
                
    def download_model(self, model_name="large-v3"):
        """检查模型是否存在，如果不存在则下载"""
        # 检查默认缓存路径
        cache_dir = os.path.expanduser("~/.cache/huggingface/hub")
        model_dir = os.path.join(cache_dir, "models--Systran--faster-whisper-large-v3", "snapshots")
        
        # 如果模型目录存在，说明已经下载过
        if os.path.exists(model_dir):
            print(f"找到已下载的模型目录: {model_dir}")
            # 获取最新的快照
            snapshots = os.listdir(model_dir)
            if snapshots:
                latest_snapshot = snapshots[0]
                model_path = os.path.join(model_dir, latest_snapshot)
                print(f"使用模型: {model_path}")
                return model_path
                
        # 如果模型不存在，使用 huggingface-cli 下载
        print("开始下载模型...")
        try:
            import subprocess
            cmd = [
                "huggingface-cli",
                "download",
                "--resume-download",
                "Systran/faster-whisper-large-v3",
                "--local-dir",
                os.path.dirname(model_dir),
                "--local-dir-use-symlinks",
                "False"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                print(f"下载失败: {result.stderr}")
                return None
                
            # 再次检查模型目录
            if os.path.exists(model_dir):
                snapshots = os.listdir(model_dir)
                if snapshots:
                    latest_snapshot = snapshots[0]
                    model_path = os.path.join(model_dir, latest_snapshot)
                    print(f"模型下载完成: {model_path}")
                    return model_path
                    
            print("模型下载失败")
            return None
            
        except Exception as e:
            print(f"下载模型失败: {str(e)}")
            return None
    
    def transcribe(self, audio_file: str, language="zh", initial_prompt=None, target_language=None) -> str:
        """使用批量模式转写音频文件，返回完整文本 - 性能优化版本"""
        try:
            self.ensure_model_loaded()
            
            # 性能优化：检查文件大小，调整参数
            file_size = os.path.getsize(audio_file)
            is_large_file = file_size > 1024 * 1024 * 5  # 5MB以上的文件
            
            try:
                self.logger.info(f"Transcribing audio file: {audio_file} ({file_size/1024/1024:.2f}MB), language: {language}, target_language: {target_language}")
                
                # 根据文件大小动态调整参数
                if is_large_file:
                    beam_size = 3  # 大文件使用更小的beam_size
                    batch_size = 8  # 增加批处理大小
                else:
                    beam_size = 1  # 小文件保持最小beam_size
                    batch_size = 4
                
                # 如果需要翻译，使用task参数
                task = "translate" if target_language and target_language != language else "transcribe"
                
                # 性能优化：记录转写开始时间
                transcribe_start = time.time()
                
                # 使用更宽松的VAD参数，特别适合虚拟音频设备和低音量输入
                segments, info = self.model.transcribe(
                    audio_file,
                    language=language if language != "auto" else None,
                    initial_prompt=initial_prompt,
                    beam_size=beam_size,
                    batch_size=batch_size,  # 新增批处理大小
                    word_timestamps=False,  # 禁用词级时间戳以减少内存使用
                    condition_on_previous_text=False,
                    temperature=0.0,
                    compression_ratio_threshold=2.4,
                    no_speech_threshold=0.3,  # 降低无语音阈值，从0.6降低到0.3
                    vad_filter=True,
                    vad_parameters={
                        "min_silence_duration_ms": 200,  # 减少最小静音时长，从500ms降低到200ms
                        "speech_pad_ms": 100,            # 语音填充，在检测到的语音前后添加填充
                        "threshold": 0.3                  # 降低VAD检测阈值，从默认0.5降低到0.3
                    },
                    task=task  # 使用task参数替代translate参数
                )
                
                # 性能优化：使用生成器和列表推导式加速文本处理
                transcript = " ".join(segment.text for segment in segments if segment.text)
                
                transcribe_time = time.time() - transcribe_start
                
                # 清理文本
                transcript = transcript.strip()
                
                # 校验结果 - 放宽条件，允许更多内容通过
                if not transcript:
                    self.logger.warning("转写结果为空")
                    return "未检测到语音内容，请确保麦克风正常工作并重试"
                elif len(transcript) < 3:  # 如果结果太短，也可能是噪音
                    self.logger.warning(f"转写结果过短: {transcript}")
                    return "检测到音频但无法识别，请说话清晰一些"
                elif "感谢使用" in transcript or "广告" in transcript:
                    self.logger.warning("转写结果包含广告内容")
                    return "请说话..."
                
                self.logger.info(f"转写成功，结果长度: {len(transcript)}, 耗时: {transcribe_time:.2f}s")
                return transcript
                
            except Exception as e:
                self.logger.error(f"转写音频过程中出错: {str(e)}")
                raise
                
        except Exception as e:
            self.logger.error(f"转写过程中出错: {str(e)}")
            return f"错误：{str(e)}"
            
        finally:
            # 确保清理所有资源
            try:
                # 不要删除模型，保持模型加载状态
                # 只进行轻量级清理
                import gc
                gc.collect()
                
            except Exception as e:
                self.logger.error(f"清理资源时出错: {str(e)}")
                
    def add_audio_chunk(self, audio_chunk: bytes) -> None:
        """添加音频数据块到缓冲区，用于实时转写"""
        self.buffer.append(audio_chunk)
        self.buffer_size += len(audio_chunk)
        
    def clear_buffer(self) -> None:
        """清空音频缓冲区"""
        self.buffer = []
        self.buffer_size = 0
        
    def get_realtime_transcription(self, language="zh", target_language=None) -> Optional[str]:
        """实时转写当前缓冲区中的音频数据 - 性能优化版本"""
        if not self.buffer or self.buffer_size == 0:
            return None
            
        try:
            self.ensure_model_loaded()
            
            # 性能优化：更智能的缓冲区管理
            if self.buffer_size > self.max_buffer_size:
                self.logger.warning("缓冲区超过最大大小限制，清理旧数据")
                # 保留最后一半的数据，而不是逐个删除
                total_chunks = len(self.buffer)
                keep_chunks = total_chunks // 2
                removed_chunks = self.buffer[:total_chunks - keep_chunks]
                self.buffer = self.buffer[total_chunks - keep_chunks:]
                
                # 重新计算缓冲区大小
                self.buffer_size = sum(len(chunk) for chunk in self.buffer)
                self.logger.debug(f"清理了 {len(removed_chunks)} 个音频块，当前缓冲区大小: {self.buffer_size}")
            
            # 性能优化：如果缓冲区数据太少，跳过转写
            min_buffer_size = 1024 * 16  # 16KB最小数据量
            if self.buffer_size < min_buffer_size:
                return None
            
            # 将缓冲区数据保存为临时文件
            temp_file_path = None
            try:
                # 创建临时文件
                with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_file:
                    temp_file_path = temp_file.name
                    
                    # 性能优化：使用更高效的WAV文件写入
                    with wave.open(temp_file_path, 'wb') as wf:
                        wf.setnchannels(1)
                        wf.setsampwidth(2)
                        wf.setframerate(16000)
                        # 一次性写入所有数据，而不是逐块写入
                        combined_data = b''.join(self.buffer)
                        wf.writeframes(combined_data)
                
                # 转写临时文件
                transcript = self.transcribe(
                    temp_file_path,
                    language=language,
                    target_language=target_language
                )
                
                return transcript
                
            finally:
                # 清理临时文件
                if temp_file_path and os.path.exists(temp_file_path):
                    try:
                        os.unlink(temp_file_path)
                    except Exception as e:
                        self.logger.warning(f"无法删除临时文件: {e}")
                        
        except Exception as e:
            self.logger.error(f"实时转写过程中出错: {str(e)}")
            return None 