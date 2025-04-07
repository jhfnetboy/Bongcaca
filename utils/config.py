import os
import json
from pathlib import Path

class Config:
    def __init__(self):
        """初始化配置"""
        self.config_dir = self._get_config_dir()
        self.config_file = os.path.join(self.config_dir, "config.json")
        self.models_dir = self._get_models_dir()
        self._ensure_models_dir()
        self.default_config = {
            "model_path": None,
            "language": "auto",
            "hotkey": "Cmd+Shift+Space",
            "theme": "light"
        }
        self.config = self._load_config()
        
    def _get_config_dir(self):
        """获取配置目录"""
        if os.name == "posix":  # macOS/Linux
            base_dir = os.path.expanduser("~/.config/voicetyper")
        else:  # Windows
            base_dir = os.path.join(os.getenv("APPDATA"), "VoiceTyper")
            
        os.makedirs(base_dir, exist_ok=True)
        return base_dir
        
    def _get_models_dir(self):
        """获取模型目录"""
        if os.name == "posix":  # macOS/Linux
            base_dir = os.path.expanduser("~/.local/share/voicetyper/models")
        else:  # Windows
            base_dir = os.path.join(os.getenv("APPDATA"), "VoiceTyper", "models")
            
        return base_dir
        
    def _ensure_models_dir(self):
        """确保模型目录存在"""
        os.makedirs(self.models_dir, exist_ok=True)
        
    def _load_config(self):
        """加载配置"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r") as f:
                    config = json.load(f)
                    # 合并默认配置和已保存的配置
                    return {**self.default_config, **config}
            except:
                return self.default_config.copy()
        return self.default_config.copy()
        
    def save(self):
        """保存配置"""
        with open(self.config_file, "w") as f:
            json.dump(self.config, f, indent=4)
            
    def get(self, key, default=None):
        """获取配置项"""
        return self.config.get(key, default)
        
    def set(self, key, value):
        """设置配置项"""
        self.config[key] = value
        self.save()
        
    def reset(self):
        """重置为默认配置"""
        self.config = self.default_config.copy()
        self.save()
        
    def get_model_path(self, model_name="medium"):
        """获取模型路径"""
        model_path = os.path.join(self.models_dir, model_name)
        return model_path if os.path.exists(model_path) else None 