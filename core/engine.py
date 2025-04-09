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
    
    def transcribe(self, audio_file: str, language: str = "zh") -> str:
        """使用批量模式转写音频文件，返回完整文本
        
        参数:
            audio_file: 音频文件路径
            language: 语言代码，如"zh"表示中文，"en"表示英文，"auto"表示自动检测
            
        返回:
            转录文本
        """
        if not os.path.exists(audio_file):
            self.logger.error(f"音频文件不存在: {audio_file}")
            return "错误：音频文件不存在"
            
        try:
            self.ensure_model_loaded()
            
            self.logger.info(f"Transcribing audio file: {audio_file}, language: {language}")
            
            # 使用单次调用转写并收集结果，避免使用迭代器
            beam_size = self.settings.get("beam_size", 5)
            
            # 创建一个本地安全的副本，避免后续引用被其他线程修改
            local_transcript = ""
            
            try:
                # 如果language是auto，让模型自动检测语言
                lang_param = None if language == "auto" else language
                
                segments, info = self.model.transcribe(
                    audio_file,
                    beam_size=beam_size,
                    language=lang_param,
                    vad_filter=True,
                    vad_parameters=dict(min_silence_duration_ms=500)
                )
                
                # 记录语言检测结果
                self.logger.info(f"Detected language: {info.language} (probability: {info.language_probability})")
                
                # 立即收集所有片段文本
                # 使用列表累积文本并连接，避免在循环中拼接字符串可能带来的问题
                text_segments = []
                for segment in segments:
                    text_segments.append(segment.text)
                    
                local_transcript = " ".join(text_segments)
                local_transcript = local_transcript.strip()
            finally:
                # 确保释放资源，防止后续访问可能导致的内存错误
                # 显式删除局部变量
                if 'segments' in locals():
                    del segments
                if 'info' in locals():
                    del info
                if 'text_segments' in locals():
                    del text_segments
            
            # 校验结果是否为空或者广告内容
            if not local_transcript or "感谢使用" in local_transcript:
                self.logger.warning("转写结果为空或全是广告内容")
                return "请说话..."
                
            return local_transcript
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
        
    def get_realtime_transcription(self, audio_file: str = None, language: str = "zh") -> str:
        """实时处理累积的音频数据，返回转录文本
        
        参数:
            audio_file: 如果提供，则直接使用该文件进行转写，否则使用内部音频缓冲区
            language: 语言代码，如"zh"表示中文，"en"表示英文，"auto"表示自动检测
            
        返回:
            转录文本
        """
        try:
            # 检查是否有足够的数据来处理
            if not self.buffer or (len(self.buffer) < 8000 and not audio_file):  # 至少需要0.5秒的数据(16000采样率)
                return ""
    
            # 如果没有提供临时音频文件，就使用累积的缓冲区
            should_delete_file = False
            if not audio_file:
                # 创建临时音频文件
                temp_audio_file = os.path.join(
                    self.temp_dir, f"temp_audio_{time.time()}.wav"
                )
                self.buffer_to_wav(temp_audio_file)
                audio_file = temp_audio_file
                should_delete_file = True
    
            # 转录临时音频文件
            result = self.transcribe(audio_file, language=language)
            
            # 如果我们创建的是临时文件，现在可以安全删除它
            if should_delete_file:
                try:
                    os.remove(audio_file)
                except:
                    self.logger.warning(f"无法删除临时音频文件: {audio_file}")
    
            return result
        except Exception as e:
            self.logger.error(f"实时转录时发生错误: {str(e)}")
            return ""

class TranscriptionEngine:
    """转录引擎 - 支持不同语言选项的音频转录"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.whisper_engine = WhisperEngine(Config())
        
    def transcribe(self, audio_file: str, language: str = "auto") -> str:
        """
        使用指定的语言转写音频文件
        
        参数:
            audio_file: 音频文件路径
            language: 语言代码，"auto"表示自动检测，"zh"表示中文，"en"表示英文，"th"表示泰文
            
        返回:
            转录文本
        """
        self.logger.info(f"使用TranscriptionEngine转写，语言设置为: {language}")
        
        if not os.path.exists(audio_file):
            self.logger.error(f"音频文件不存在: {audio_file}")
            return "错误：音频文件不存在"
        
        try:
            # 根据语言设置调整转写参数
            lang_code = None
            if language == "zh" or language == "中文":
                lang_code = "zh"
            elif language == "en" or language == "英文":
                lang_code = "en"
            elif language == "th" or language == "泰文":
                lang_code = "th"
            # auto模式下不设置语言，让引擎自动检测
            
            # 调用底层引擎完成转写
            transcript = self.whisper_engine.transcribe(audio_file, lang_code)
            return transcript
        except Exception as e:
            self.logger.error(f"转写过程出错: {str(e)}")
            return f"错误：{str(e)}"
            
    def download_model(self, model_name: str) -> bool:
        """
        下载指定的模型
        
        参数:
            model_name: 模型名称
            
        返回:
            下载成功与否
        """
        try:
            self.logger.info(f"开始下载模型: {model_name}")
            # 委托给底层引擎完成下载
            return self.whisper_engine.download_model(model_name)
        except Exception as e:
            self.logger.error(f"下载模型失败: {str(e)}")
            return False 