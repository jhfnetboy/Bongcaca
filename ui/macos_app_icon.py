import os
import sys
import tempfile
import subprocess
from pathlib import Path
import logging
from ui.logo import create_logo_pixmap

logger = logging.getLogger(__name__)

def create_macos_app_icon():
    """
    创建MacOS系统应用图标（.icns文件）
    该图标会显示在程序坞、启动器等系统位置
    """
    try:
        logger.debug("开始创建MacOS应用图标")
        
        # 检查是否是MacOS系统
        if sys.platform != "darwin":
            logger.warning("不是MacOS系统，跳过创建图标")
            return False
        
        # 创建图标存储目录
        icon_path = Path.home() / ".voice_typer" / "icon"
        icon_path.mkdir(parents=True, exist_ok=True)
        
        icns_file = icon_path / "VoiceTyper.icns"
        
        # 如果图标已经存在，直接返回路径
        if icns_file.exists():
            logger.debug(f"MacOS图标已存在: {icns_file}")
            return str(icns_file)
        
        # 创建临时目录
        with tempfile.TemporaryDirectory() as temp_dir:
            # 生成不同尺寸的图标
            icon_dir = Path(temp_dir) / "VoiceTyper.iconset"
            icon_dir.mkdir(exist_ok=True)
            
            # 所需的尺寸
            sizes = [16, 32, 64, 128, 256, 512, 1024]
            
            # 生成各种尺寸的图标
            for size in sizes:
                # 生成1x尺寸
                pixmap = create_logo_pixmap(size)
                icon_file = icon_dir / f"icon_{size}x{size}.png"
                pixmap.save(str(icon_file))
                
                # 生成2x尺寸(Retina)
                if size <= 512:  # 1024已经是最大的了
                    pixmap_2x = create_logo_pixmap(size * 2)
                    icon_file_2x = icon_dir / f"icon_{size}x{size}@2x.png"
                    pixmap_2x.save(str(icon_file_2x))
            
            # 使用iconutil命令生成.icns文件
            subprocess.run(["iconutil", "-c", "icns", "-o", str(icns_file), str(icon_dir)], 
                           check=True, capture_output=True)
            
            logger.info(f"成功创建MacOS应用图标: {icns_file}")
            return str(icns_file)
    
    except Exception as e:
        logger.error(f"创建MacOS应用图标失败: {e}")
        return False

def register_dock_icon(qapp):
    """
    为QApplication注册MacOS Dock图标
    """
    if sys.platform != "darwin":
        return
    
    try:
        from PySide6.QtGui import QIcon
        
        # 生成或获取图标
        icns_path = create_macos_app_icon()
        if icns_path and os.path.exists(icns_path):
            # 设置应用程序图标
            qapp.setWindowIcon(QIcon(icns_path))
            
            # 特殊设置MacOS Dock图标
            # 由于PySide6直接设置即可，不需要额外代码
            logger.debug("MacOS Dock图标已注册")
    except Exception as e:
        logger.error(f"注册MacOS Dock图标失败: {e}") 