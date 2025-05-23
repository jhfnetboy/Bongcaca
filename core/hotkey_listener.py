import logging
from Quartz import (
    CFMachPortCreateRunLoopSource,
    CFRunLoopGetCurrent,
    CFRunLoopAddSource,
    CFRunLoopRun,
    CGEventTapCreate,
    CGEventMaskBit,
    kCGEventFlagMaskSecondaryFn,
    kCGEventKeyDown,
    kCGEventKeyUp,
    kCGSessionEventTap,
    kCGHeadInsertEventTap,
)
import time
import threading
import os

class HotkeyListener:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.is_running = False
        self.last_fn_press = 0
        self.callback = None
        self.thread = None
        
    def _play_start_sound(self):
        """播放开始录音提示音"""
        try:
            os.system('afplay /System/Library/Sounds/Ping.aiff')
        except Exception as e:
            self.logger.error(f"播放开始提示音失败: {e}")
            
    def _play_complete_sound(self):
        """播放完成提示音"""
        try:
            os.system('afplay /System/Library/Sounds/Glass.aiff')
        except Exception as e:
            self.logger.error(f"播放完成提示音失败: {e}")

    def _event_callback(self, proxy, event_type, event, refcon):
        """处理键盘事件"""
        try:
            # 检查是否是 fn 键事件
            if event_type in [kCGEventKeyDown, kCGEventKeyUp]:
                flags = CGEventGetFlags(event)
                if flags & kCGEventFlagMaskSecondaryFn:
                    current_time = time.time()
                    if current_time - self.last_fn_press < 0.3:  # 300ms内的双击
                        self.logger.info("检测到fn键双击")
                        if self.callback:
                            self.callback()
                    self.last_fn_press = current_time
        except Exception as e:
            self.logger.error(f"处理键盘事件时出错: {e}")
            
        return event  # 继续传递事件给其他应用
        
    def _run_event_tap(self):
        """运行事件监听循环"""
        try:
            # 创建事件监听
            tap = CGEventTapCreate(
                kCGSessionEventTap,
                kCGHeadInsertEventTap,
                0,
                CGEventMaskBit(kCGEventKeyDown) | CGEventMaskBit(kCGEventKeyUp),
                self._event_callback,
                None
            )
            
            if tap:
                # 创建运行循环源
                run_loop_source = CFMachPortCreateRunLoopSource(None, tap, 0)
                # 获取当前运行循环
                run_loop = CFRunLoopGetCurrent()
                # 添加源
                CFRunLoopAddSource(run_loop, run_loop_source, kCFRunLoopCommonModes)
                # 启动运行循环
                CFRunLoopRun()
            else:
                self.logger.error("创建事件监听失败")
                
        except Exception as e:
            self.logger.error(f"运行事件监听时出错: {e}")
            
    def start(self, callback):
        """启动快捷键监听
        Args:
            callback: fn键双击时触发的回调函数
        """
        if self.is_running:
            return
            
        self.callback = callback
        self.is_running = True
        
        # 在新线程中运行事件监听
        self.thread = threading.Thread(target=self._run_event_tap)
        self.thread.daemon = True
        self.thread.start()
        
        self.logger.info("全局快捷键监听已启动")
        
    def stop(self):
        """停止快捷键监听"""
        self.is_running = False
        if self.thread:
            self.thread.join(timeout=1.0)
        self.logger.info("全局快捷键监听已停止")