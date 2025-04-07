class PlatformIntegration:
    """平台集成基类，定义接口"""
    
    def register_hotkey(self, key_combo, callback):
        """注册全局热键"""
        raise NotImplementedError
        
    def unregister_hotkey(self, key_combo):
        """注销全局热键"""
        raise NotImplementedError
        
    def insert_text(self, text):
        """向当前活跃窗口插入文本"""
        raise NotImplementedError
        
    def get_active_app(self):
        """获取当前活跃应用信息"""
        raise NotImplementedError 