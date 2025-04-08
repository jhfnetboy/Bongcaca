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
        
        # 强制重新生成图标，解决图标不显示问题
        if icns_file.exists():
            logger.debug(f"删除旧的MacOS图标: {icns_file}")
            icns_file.unlink()
        
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
                logger.debug(f"生成图标: {icon_file}")
                
                # 生成2x尺寸(Retina)
                if size <= 512:  # 1024已经是最大的了
                    pixmap_2x = create_logo_pixmap(size * 2)
                    icon_file_2x = icon_dir / f"icon_{size}x{size}@2x.png"
                    pixmap_2x.save(str(icon_file_2x))
                    logger.debug(f"生成Retina图标: {icon_file_2x}")
            
            # 确保临时目录中的图标文件都已正确生成
            if not any(icon_dir.glob("*.png")):
                logger.error("临时目录中没有找到任何PNG图标文件")
                return False
                
            # 使用iconutil命令生成.icns文件
            try:
                cmd = ["iconutil", "-c", "icns", "-o", str(icns_file), str(icon_dir)]
                logger.debug(f"执行命令: {' '.join(cmd)}")
                result = subprocess.run(cmd, check=True, capture_output=True)
                logger.debug(f"命令输出: {result.stdout.decode()}")
                
                if not icns_file.exists() or icns_file.stat().st_size == 0:
                    logger.error(f"图标文件未生成或为空: {icns_file}")
                    return False
                    
                logger.info(f"成功创建MacOS应用图标: {icns_file}")
                return str(icns_file)
            except subprocess.CalledProcessError as e:
                logger.error(f"iconutil命令执行失败: {e.stderr.decode() if e.stderr else str(e)}")
                
                # 尝试使用备用方法生成图标
                logger.debug("尝试使用sips命令生成图标")
                try:
                    # 复制一个PNG图标作为备用
                    fallback_icon = icon_path / "VoiceTyper.png"
                    biggest_icon = list(icon_dir.glob("*1024*.png"))
                    if biggest_icon:
                        import shutil
                        shutil.copy(str(biggest_icon[0]), str(fallback_icon))
                        logger.info(f"已创建备用PNG图标: {fallback_icon}")
                        return str(fallback_icon)
                except Exception as e2:
                    logger.error(f"备用方法也失败: {e2}")
                return False
    
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