from faster_whisper import WhisperModel
import os
import logging
from huggingface_hub import snapshot_download
import psutil
from utils.config import Config

class WhisperEngine:
    def __init__(self, config: Config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.model = None
        self.model_name = None
        self.settings = None
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
        
    def get_optimal_settings(self):
        """获取最优的模型和设置"""
        # 检查是否已下载large-v3模型
        large_v3_path = os.path.expanduser("~/.cache/huggingface/hub/models--Systran--faster-whisper-large-v3")
        if os.path.exists(large_v3_path):
            self.logger.info("Using large-v3 model")
            self.model_name = "large-v3"
            self.settings = {
                "device": "cuda" if self._has_gpu() else "cpu",
                "compute_type": "float16" if self._has_gpu() else "int8",
                "beam_size": 5
            }
            return
            
        # 如果没有large-v3,根据系统资源选择模型
        memory = psutil.virtual_memory().total / (1024**3)  # GB
        cpu_count = psutil.cpu_count()
        
        if memory >= 16 and cpu_count >= 4:
            self.model_name = "medium"
            self.settings = {
                "device": "cuda" if self._has_gpu() else "cpu",
                "compute_type": "float16" if self._has_gpu() else "int8",
                "beam_size": 5
            }
        else:
            self.model_name = "small"
            self.settings = {
                "device": "cuda" if self._has_gpu() else "cpu",
                "compute_type": "float16" if self._has_gpu() else "int8",
                "beam_size": 5
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
        if self.model is None:
            self.get_optimal_settings()
            self.logger.info(f"Loading model: {self.model_name} with settings: {self.settings}")
            
            # 根据官方示例调用WhisperModel
            try:
                self.model = WhisperModel(
                    self.model_name,  # 使用模型名称,而不是路径
                    device=self.settings["device"],
                    compute_type=self.settings["compute_type"]
                )
                self.logger.info("模型加载成功")
            except Exception as e:
                self.logger.error(f"模型加载失败: {e}")
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
    
    def transcribe(self, audio_file: str):
        """转录音频文件"""
        self.ensure_model_loaded()
        self.logger.info(f"Transcribing audio file: {audio_file}")
        
        try:
            # 设置语言为中文
            segments, info = self.model.transcribe(
                audio_file,
                beam_size=self.settings["beam_size"],
                language="zh",  # 指定中文
                vad_filter=True,  # 添加语音活动检测
                condition_on_previous_text=False,  # 关闭基于之前文本的条件
                suppress_blank=True,  # 抑制空白
                no_speech_threshold=0.6  # 提高无语音阈值
            )
            
            # 获取检测到的语言
            self.logger.info(f"Detected language: {info.language} (probability: {info.language_probability})")
            
            # 收集所有文本片段,并过滤掉广告内容
            text = ""
            segments_list = list(segments)  # 将生成器转换为列表
            
            for segment in segments_list:
                # 过滤掉已知的广告内容
                if "字幕由" in segment.text or "Amara.org" in segment.text or "社群提供" in segment.text or "字幕志愿者" in segment.text:
                    self.logger.warning(f"过滤广告内容: {segment.text}")
                    continue
                
                self.logger.debug(f"[{segment.start:.2f}s -> {segment.end:.2f}s] {segment.text}")
                text += segment.text + " "
                
            filtered_text = text.strip()
            if not filtered_text:
                self.logger.warning("转写结果为空或全是广告内容")
                return "请说话..."
                
            return filtered_text
            
        except Exception as e:
            self.logger.error(f"Transcription failed: {e}")
            raise 