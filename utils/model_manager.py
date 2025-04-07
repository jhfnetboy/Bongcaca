import os
import shutil
from huggingface_hub import snapshot_download
import logging
import psutil

class ModelManager:
    def __init__(self, config):
        """初始化模型管理器"""
        self.config = config
        logging.basicConfig()
        logging.getLogger("faster_whisper").setLevel(logging.INFO)
        
    def download_model(self, model_name="medium"):
        """下载指定模型"""
        print(f"开始下载模型: {model_name}")
        
        try:
            # 构建Hugging Face仓库ID
            repo_id = f"guillaumekln/faster-whisper-{model_name}"
            
            # 下载模型
            model_path = snapshot_download(
                repo_id=repo_id,
                local_dir=os.path.join(self.config.models_dir, model_name),
                local_dir_use_symlinks=False,
                revision="main",
                ignore_patterns=["*.msgpack", "*.safetensors"]  # 忽略不需要的文件
            )
            
            print(f"模型 {model_name} 下载完成")
            return model_path
            
        except Exception as e:
            print(f"下载模型 {model_name} 失败: {str(e)}")
            if os.path.exists(os.path.join(self.config.models_dir, model_name)):
                shutil.rmtree(os.path.join(self.config.models_dir, model_name))
            return None
            
    def get_available_models(self):
        """获取可用的模型列表"""
        return ["tiny", "base", "small", "medium", "large-v1", "large-v2", "large-v3"]
        
    def get_recommended_model(self):
        """根据系统配置推荐合适的模型"""
        memory_gb = psutil.virtual_memory().total / (1024 * 1024 * 1024)
        
        if memory_gb >= 16:
            return "large-v3"
        elif memory_gb >= 8:
            return "medium"
        elif memory_gb >= 4:
            return "small"
        else:
            return "tiny" 