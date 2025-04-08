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
        self._detect_models()
        
    def _detect_models(self):
        """检测已下载的模型"""
        self.logger.info("Detecting downloaded models...")
        
        # 检查large-v3模型
        large_v3_path = os.path.expanduser("~/.cache/huggingface/hub/models--Systran--faster-whisper-large-v3")
        if os.path.exists(large_v3_path):
            self.logger.info(f"Found large-v3 model at: {large_v3_path}")
            self.logger.info("Using large-v3 model")
            return {
                "model_name": "large-v3",
                "compute_type": "int8",
                "device": "cpu",
                "threads": min(psutil.cpu_count(), 4),
                "batch_size": 1
            }
            
        # 检查medium模型
        medium_path = os.path.expanduser("~/.cache/huggingface/hub/models--Systran--faster-whisper-medium")
        if os.path.exists(medium_path):
            self.logger.info(f"Found medium model at: {medium_path}")
            self.logger.info("Using medium model")
            return {
                "model_name": "medium",
                "compute_type": "int8",
                "device": "cpu",
                "threads": min(psutil.cpu_count(), 4),
                "batch_size": 1
            }
            
        # 检查small模型
        small_path = os.path.expanduser("~/.cache/huggingface/hub/models--Systran--faster-whisper-small")
        if os.path.exists(small_path):
            self.logger.info(f"Found small model at: {small_path}")
            self.logger.info("Using small model")
            return {
                "model_name": "small",
                "compute_type": "int8",
                "device": "cpu",
                "threads": min(psutil.cpu_count(), 2),
                "batch_size": 1
            }
            
        self.logger.warning("No downloaded models found")
        return None
        
    def get_optimal_settings(self) -> Dict[str, Any]:
        """根据系统资源情况，优化配置参数"""
        # 检查系统内存和CPU
        system_ram = psutil.virtual_memory().total / (1024 ** 3)  # GB
        cpu_count = psutil.cpu_count(logical=False)
        if cpu_count is None:
            cpu_count = psutil.cpu_count(logical=True)
            if cpu_count is None:
                cpu_count = 2
                
        self.logger.info("Detecting downloaded models...")
        # 检查是否已下载大模型
        large_model_path = os.path.expanduser("~/.cache/huggingface/hub/models--Systran--faster-whisper-large-v3")
        if os.path.exists(large_model_path):
            self.logger.info(f"Found large-v3 model at: {large_model_path}")
            model_name = "large-v3"
            compute_type = "int8"
            beam_size = 5
        # 如果系统内存>=16GB且CPU核心数>=8，使用medium模型
        elif system_ram >= 16 and cpu_count >= 8:
            self.logger.info(f"System has {system_ram:.1f} GB RAM and {cpu_count} CPU cores. Using medium model.")
            model_name = "medium"
            compute_type = "int8"
            beam_size = 5
        # 如果系统内存>=8GB且CPU核心数>=4，使用small模型
        elif system_ram >= 8 and cpu_count >= 4:
            self.logger.info(f"System has {system_ram:.1f} GB RAM and {cpu_count} CPU cores. Using small model.")
            model_name = "small"
            compute_type = "int8"
            beam_size = 5
        # 否则使用tiny模型
        else:
            self.logger.info(f"System has {system_ram:.1f} GB RAM and {cpu_count} CPU cores. Using tiny model.")
            model_name = "tiny"
            compute_type = "int8"
            beam_size = 3
            
        self.logger.info(f"Using {model_name} model")
        
        # 确定是否使用GPU
        device = "cpu"  # 默认使用CPU
        
        # 如果有足够内存的NVIDIA GPU，可以考虑使用cuda
        # TODO: 检测GPU并自动配置
        
        return {
            "model_name": model_name,
            "device": device,
            "compute_type": compute_type,
            "beam_size": beam_size
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
        
        try:
            from faster_whisper import WhisperModel
            
            self.logger.info(f"Loading model: {model_name} with settings: {self.settings}")
            self.model = WhisperModel(
                model_size_or_path=model_name,
                device=device,
                compute_type=compute_type,
                download_root=self.config.models_dir if hasattr(self.config, "models_dir") else None
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
    
    def transcribe(self, audio_file: str) -> str:
        """使用批量模式转写音频文件，返回完整文本"""
        if not os.path.exists(audio_file):
            self.logger.error(f"音频文件不存在: {audio_file}")
            return "错误：音频文件不存在"
            
        try:
            self.ensure_model_loaded()
            
            self.logger.info(f"Transcribing audio file: {audio_file}")
            
            # 转写音频
            beam_size = self.settings.get("beam_size", 5)
            segments, info = self.model.transcribe(
                audio_file,
                beam_size=beam_size,
                language="zh",
                vad_filter=True,
                vad_parameters=dict(min_silence_duration_ms=500)
            )
            
            # 记录语言检测结果
            self.logger.info(f"Detected language: {info.language} (probability: {info.language_probability})")
            
            # 合并所有片段
            transcript = ""
            for segment in segments:
                transcript += segment.text + " "
                
            # 清理文本
            transcript = transcript.strip()
            
            # 校验结果是否为空或者广告内容
            if not transcript or "感谢使用" in transcript:
                self.logger.warning("转写结果为空或全是广告内容")
                return "请说话..."
                
            return transcript
        except Exception as e:
            self.logger.error(f"转写过程中出错: {str(e)}")
            return f"错误：{str(e)}"
            
    def add_audio_chunk(self, audio_chunk: bytes) -> None:
        """添加音频数据块到缓冲区，用于实时转写"""
        self.buffer.append(audio_chunk)
        self.buffer_size += len(audio_chunk)
        
    def clear_buffer(self) -> None:
        """清空音频缓冲区"""
        self.buffer = []
        self.buffer_size = 0
        
    def get_realtime_transcription(self) -> Optional[str]:
        """实时转写当前缓冲区中的音频数据"""
        if not self.buffer or self.buffer_size == 0:
            return None
            
        try:
            self.ensure_model_loaded()

            # 如果缓冲区太小，可能无法有效识别
            if self.buffer_size < 8000:  # 至少需要0.5秒的音频(16000Hz采样率，16位)
                return None
                
            # 将缓冲区数据保存为临时文件
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                temp_file_path = temp_file.name
                
                try:
                    # 写入WAV头
                    import wave
                    wf = wave.open(temp_file_path, 'wb')
                    wf.setnchannels(1)
                    wf.setsampwidth(2)  # 16-bit
                    wf.setframerate(16000)
                    
                    # 合并所有缓冲区数据
                    all_audio_data = b''.join(self.buffer)
                    wf.writeframes(all_audio_data)
                    wf.close()
                    
                    # 转写临时文件
                    beam_size = self.settings.get("beam_size", 5)
                    segments, info = self.model.transcribe(
                        temp_file_path,
                        beam_size=3,  # 使用较小的beam size以提高速度
                        language="zh",
                        vad_filter=True,
                        vad_parameters=dict(min_silence_duration_ms=300),  # 减少静音判断时间
                        word_timestamps=False,  # 不需要单词级时间戳
                        condition_on_previous_text=True,  # 利用上下文改善实时体验
                        no_speech_threshold=0.3,  # 降低无语音阈值，更积极地识别
                    )
                    
                    # 提取文本
                    transcript = ""
                    for segment in segments:
                        transcript += segment.text + " "
                    
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
                    try:
                        os.unlink(temp_file_path)
                    except:
                        pass
                    
        except Exception as e:
            self.logger.error(f"实时转写过程中出错: {str(e)}")
            return None 