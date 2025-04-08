"""
应用程序logo资源
"""
from PySide6.QtGui import QIcon, QPixmap, QPainter, QColor, QFont, QBrush, QPen, QPainterPath
from PySide6.QtCore import Qt, QSize

def create_logo_pixmap(size=128):
    """创建应用程序logo的pixmap"""
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)
    
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    
    # 绘制圆形背景
    painter.setPen(Qt.NoPen)
    painter.setBrush(QBrush(QColor(48, 48, 48)))
    painter.drawEllipse(0, 0, size, size)
    
    # 绘制喇叭图标
    painter.setPen(QPen(QColor(255, 100, 200), 3))
    painter.setBrush(QBrush(QColor(255, 100, 200, 150)))
    
    # 喇叭主体
    center_x = size / 2
    center_y = size / 2
    speaker_width = size * 0.4
    speaker_height = size * 0.5
    
    path = QPainterPath()
    path.moveTo(center_x - speaker_width/2, center_y - speaker_height/4)
    path.lineTo(center_x - speaker_width/4, center_y - speaker_height/4)
    path.lineTo(center_x + speaker_width/4, center_y - speaker_height/2)
    path.lineTo(center_x + speaker_width/4, center_y + speaker_height/2)
    path.lineTo(center_x - speaker_width/4, center_y + speaker_height/4)
    path.lineTo(center_x - speaker_width/2, center_y + speaker_height/4)
    path.closeSubpath()
    
    painter.drawPath(path)
    
    # 音波
    wave_radius1 = size * 0.55
    wave_radius2 = size * 0.7
    painter.setPen(QPen(QColor(255, 100, 200), 2))
    painter.drawArc(center_x - wave_radius1/2, center_y - wave_radius1/2, 
                   wave_radius1, wave_radius1, -45 * 16, 90 * 16)
    painter.drawArc(center_x - wave_radius2/2, center_y - wave_radius2/2, 
                   wave_radius2, wave_radius2, -45 * 16, 90 * 16)
    
    # 添加BCC文字
    font = QFont("Arial", size/5, QFont.Bold)
    painter.setFont(font)
    painter.setPen(QPen(QColor(255, 255, 255)))
    painter.drawText(size/8, size * 7/8, "BCC")
    
    painter.end()
    return pixmap

def create_app_icon():
    """创建应用程序图标"""
    icon = QIcon()
    for size in [16, 32, 64, 128, 256]:
        icon.addPixmap(create_logo_pixmap(size))
    return icon 