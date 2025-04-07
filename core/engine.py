from faster_whisper import WhisperModel
import os
import logging
from huggingface_hub import snapshot_download

class WhisperEngine:
    def __init__(self, model_path=None, settings=None):
        """初始化引擎但不立即加载模型"""
        # 如果未指定模型路径，使用默认缓存路径
        if model_path is None:
            model_path = os.path.expanduser("~/.cache/huggingface/hub/models--Systran--faster-whisper-large-v3/snapshots/edaa852ec7e145841d8ffdb056a99866b5f0a478")
            
        self.model_path = model_path
        self.settings = settings or self.get_optimal_settings()
        self.model = None
        
        # 配置日志
        logging.basicConfig()
        logging.getLogger("faster_whisper").setLevel(logging.INFO)
        
    def get_optimal_settings(self):
        """根据系统配置获取最佳性能设置"""
        import psutil
        
        settings = {
            "compute_type": "int8",  # 所有设备默认使用int8量化
            "device": "cpu",         # 使用CPU推理
            "threads": min(psutil.cpu_count(), 4),  # 使用最多4个线程，避免系统卡顿
            "batch_size": 1          # 默认批处理大小
        }
        
        # 根据CPU核心数调整
        if psutil.cpu_count(logical=False) >= 8:  # 8核心及以上
            settings["threads"] = min(psutil.cpu_count() // 2, 8)
            settings["batch_size"] = 4
        
        # 根据内存调整批处理大小
        memory_gb = psutil.virtual_memory().total / (1024 * 1024 * 1024)
        if memory_gb >= 12:
            settings["batch_size"] = 8
            
        return settings
        
    def ensure_model_loaded(self):
        """确保模型已加载"""
        if self.model is None:
            print("加载语音识别模型中...")
            try:
                self.model = WhisperModel(
                    self.model_path,
                    device=self.settings["device"],
                    compute_type=self.settings["compute_type"],
                    cpu_threads=self.settings["threads"]
                )
                print("模型加载完成")
            except Exception as e:
                print(f"模型加载失败: {str(e)}")
                raise
    
    def download_model(self, model_name="large-v3"):
        """检查模型是否存在，如果不存在则下载"""
        # 检查默认缓存路径
        default_path = os.path.expanduser("~/.cache/huggingface/hub/models--Systran--faster-whisper-large-v3/snapshots/edaa852ec7e145841d8ffdb056a99866b5f0a478")
        if os.path.exists(default_path):
            print(f"找到已下载的模型: {default_path}")
            return default_path
            
        print(f"开始下载模型: {model_name}")
        try:
            # 使用 huggingface-cli 下载模型
            import subprocess
            cmd = [
                "huggingface-cli",
                "download",
                "--resume-download",
                f"Systran/faster-whisper-{model_name}",
                "--local-dir",
                os.path.dirname(os.path.dirname(default_path)),
                "--local-dir-use-symlinks",
                "False"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                print(f"下载失败: {result.stderr}")
                return None
                
            print(f"模型 {model_name} 下载完成")
            return default_path
            
        except Exception as e:
            print(f"下载模型 {model_name} 失败: {str(e)}")
            return None
    
    def transcribe(self, audio_file, language=None):
        """转写音频文件"""
        self.ensure_model_loaded()
        
        segments, info = self.model.transcribe(
            audio_file,
            language=language,
            beam_size=5,
            vad_filter=self.settings.get("vad_filter", True),
            vad_parameters=self.settings.get("vad_parameters", {}),
            batch_size=self.settings.get("batch_size", 1)
        )
        
        # 收集所有文本段落
        text_segments = []
        for segment in segments:
            text_segments.append(segment.text.strip())
        
        return " ".join(text_segments), info 