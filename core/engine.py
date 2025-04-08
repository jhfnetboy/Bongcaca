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
        
        # 检查是否已下载large-v3模型
        large_v3_path = os.path.expanduser("~/.cache/huggingface/hub/models--Systran--faster-whisper-large-v3")
        if os.path.exists(large_v3_path):
            print("Using large-v3 model")
            return {
                "model_name": "large-v3",
                "compute_type": "int8",
                "device": "cpu",
                "threads": min(psutil.cpu_count(), 4),
                "batch_size": 1
            }
            
        # 如果没有large-v3，根据系统配置选择
        memory_gb = psutil.virtual_memory().total / (1024 * 1024 * 1024)
        cpu_count = psutil.cpu_count(logical=False)
        
        if memory_gb >= 16 and cpu_count >= 8:
            print("Using large-v3 model (recommended for your system)")
            return {
                "model_name": "large-v3",
                "compute_type": "int8",
                "device": "cpu",
                "threads": min(cpu_count, 8),
                "batch_size": 4
            }
        elif memory_gb >= 8 and cpu_count >= 4:
            print("Using medium model (recommended for your system)")
            return {
                "model_name": "medium",
                "compute_type": "int8",
                "device": "cpu",
                "threads": min(cpu_count, 4),
                "batch_size": 2
            }
        else:
            print("Using small model (recommended for your system)")
            return {
                "model_name": "small",
                "compute_type": "int8",
                "device": "cpu",
                "threads": min(cpu_count, 2),
                "batch_size": 1
            }
        
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