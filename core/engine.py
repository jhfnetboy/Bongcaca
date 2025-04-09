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
        """确保模型已加载"""
        if self.model is not None:
            return
            
        # 获取最优配置
        if not self.settings:
            self.settings = self.get_optimal_settings()
            
        model_name = self.settings["model_name"]
        device = self.settings["device"]
        compute_type = self.settings["compute_type"]
        beam_size = self.settings["beam_size"]
        threads = self.settings.get("threads", min(psutil.cpu_count(), 4))
        
        try:
            from faster_whisper import WhisperModel
            
            self.logger.info(f"Loading model: {model_name} with settings: {self.settings}")
            self.model = WhisperModel(
                model_size_or_path=model_name,
                device=device,
                compute_type=compute_type,
                download_root=self.config.models_dir if hasattr(self.config, "models_dir") else None,
                cpu_threads=threads
            )
            self.model_name = model_name
            self.initialized = True
            self.logger.info("模型加载成功")
        except Exception as e:
            self.logger.error(f"加载模型失败: {e}")
            raise
                
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
    
    def transcribe(self, audio_file, language=None, realtime_mode=False):
        """转写音频文件
        
        Args:
            audio_file: 音频文件路径
            language: 语言代码，如果为None或"auto"则使用中文
            realtime_mode: 是否使用实时转写模式
            
        Returns:
            str: 转写文本，如果转写失败则返回None
        """
        if not os.path.exists(audio_file):
            self.logger.error(f"Audio file not found: {audio_file}")
            return None
            
        try:
            # 记录开始时间
            start_time = time.time()
            
            # 加载模型
            if not self.model:
                self.ensure_model_loaded()
                
            # 设置默认语言为中文
            if language is None or language == "auto":
                language = "zh"
                
            self.logger.info(f"Transcribing audio file: {audio_file}, language: {language}")
            
            # 转写音频
            segments, info = self.model.transcribe(
                audio_file,
                language=language,
                beam_size=5,
                vad_filter=True,
                vad_parameters=dict(min_silence_duration_ms=500)
            )
            
            # 记录结束时间
            end_time = time.time()
            transcribe_time = end_time - start_time
            
            # 检查语言检测结果
            detected_language = info.language
            language_probability = info.language_probability
            self.logger.info(f"Detected language: {detected_language} (probability: {language_probability})")
            
            # 合并所有片段
            text_segments = []
            for segment in segments:
                if segment and segment.text and segment.text.strip():
                    text_segments.append(segment.text.strip())
            
            # 如果没有有效的文本段落，返回None
            if not text_segments:
                self.logger.warning("转写结果为空")
                return None
            
            # 合并文本段落
            text = " ".join(text_segments)
            
            # 记录转写统计信息
            self.logger.info(f"转写统计信息：")
            self.logger.info(f"- 转写时间: {transcribe_time:.2f}秒")
            self.logger.info(f"- 使用模型: {self.model_name}")
            self.logger.info(f"- 语言: {detected_language}")
            self.logger.info(f"- 文本长度: {len(text)}")
            
            return text
            
        except Exception as e:
            self.logger.error(f"Error transcribing audio: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
            return None
            
    def add_audio_chunk(self, audio_chunk: bytes) -> None:
        """添加音频数据块到缓冲区，用于实时转写"""
        self.buffer.append(audio_chunk)
        self.buffer_size += len(audio_chunk)
        
    def clear_buffer(self) -> None:
        """清空音频缓冲区"""
        self.buffer = []
        self.buffer_size = 0
        
    def get_realtime_transcription(self, language="zh", target_language=None) -> Optional[str]:
        """实时转写当前缓冲区中的音频数据
        Args:
            language: 音频的语言，默认为zh（中文），设置为auto则自动检测
            target_language: 目标语言代码，用于翻译
        """
        if not self.buffer or self.buffer_size == 0:
            return None
            
        try:
            self.ensure_model_loaded()

            # 如果缓冲区太小，可能无法有效识别
            if self.buffer_size < 8000:  # 至少需要0.5秒的音频(16000Hz采样率，16位)
                return None
                
            # 将缓冲区数据保存为临时文件
            temp_file_path = None
            try:
                # 使用更安全的方式处理临时文件
                temp_dir = tempfile.gettempdir()
                temp_file_path = os.path.join(temp_dir, f"whisper_temp_{int(time.time()*1000)}.wav")
                
                # 写入WAV头
                wf = wave.open(temp_file_path, 'wb')
                wf.setnchannels(1)
                wf.setsampwidth(2)  # 16-bit
                wf.setframerate(16000)
                
                # 创建并写入缓冲区数据的副本，避免原始数据被修改
                buffer_copy = self.buffer.copy()
                all_audio_data = b''.join(buffer_copy)
                wf.writeframes(all_audio_data)
                wf.close()
                
                # 转写临时文件
                beam_size = self.settings.get("beam_size", 5)
                
                # 根据是否需要翻译设置任务类型和参数
                if target_language and target_language != language:
                    # 翻译任务
                    task = "translate"
                    # 确保faster-whisper使用正确的语言参数
                    segments, info = self.model.transcribe(
                        temp_file_path,
                        beam_size=3,  # 使用较小的beam size以提高速度
                        language=None if language == "auto" else language,  # 源语言
                        task=task,  # 翻译任务
                        vad_filter=True,
                        vad_parameters=dict(min_silence_duration_ms=300),  # 减少静音判断时间
                        word_timestamps=False,  # 不需要单词级时间戳
                        condition_on_previous_text=True,  # 利用上下文改善实时体验
                        no_speech_threshold=0.3,  # 降低无语音阈值，更积极地识别
                        # 明确指定翻译目标语言
                        translate_to=target_language
                    )
                else:
                    # 普通转写任务
                    task = "transcribe"
                    segments, info = self.model.transcribe(
                        temp_file_path,
                        beam_size=3,  # 使用较小的beam size以提高速度
                        language=None if language == "auto" else language,
                        task=task,
                        vad_filter=True,
                        vad_parameters=dict(min_silence_duration_ms=300),  # 减少静音判断时间
                        word_timestamps=False,  # 不需要单词级时间戳
                        condition_on_previous_text=True,  # 利用上下文改善实时体验
                        no_speech_threshold=0.3,  # 降低无语音阈值，更积极地识别
                    )
                
                # 立即提取文本并释放segments引用
                transcript = ""
                for segment in segments:
                    transcript += segment.text + " "
                
                # 显式释放资源
                del segments
                del info
                del buffer_copy
                
                transcript = transcript.strip()
                
                # 结果处理
                if not transcript:
                    return None
                    
                return transcript
            except Exception as e:
                self.logger.error(f"实时转写音频文件处理过程中出错: {str(e)}")
                return None
            finally:
                # 确保临时文件被删除
                if temp_file_path and os.path.exists(temp_file_path):
                    try:
                        os.unlink(temp_file_path)
                    except Exception as cleanup_err:
                        self.logger.warning(f"无法删除临时文件: {cleanup_err}")
                
        except Exception as e:
            self.logger.error(f"实时转写过程中出错: {str(e)}")
            return None 