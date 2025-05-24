#!/usr/bin/env python3
"""
测试打包后应用的权限检查功能
"""

import sys
import os
import platform

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_bundle_id_detection():
    """测试bundle ID检测功能"""
    print("=" * 60)
    print("测试 Bundle ID 检测功能")
    print("=" * 60)
    
    from utils.permissions import get_current_bundle_id
    
    bundle_id = get_current_bundle_id()
    python_path = sys.executable
    
    print(f"Python 可执行文件路径: {python_path}")
    print(f"检测到的 Bundle ID: {bundle_id}")
    
    # 判断运行环境
    if '.app/Contents/MacOS/' in python_path:
        print("✅ 正确检测到打包应用环境")
        expected_bundle_id = 'com.bongcaca.voicetyper'
        if bundle_id == expected_bundle_id:
            print(f"✅ Bundle ID 正确: {bundle_id}")
        else:
            print(f"❌ Bundle ID 不正确，期望: {expected_bundle_id}，实际: {bundle_id}")
    else:
        print("ℹ️  运行在开发环境中")
    
    return bundle_id

def test_tcc_permission_check():
    """测试TCC权限检查"""
    print("\n" + "=" * 60)
    print("测试 TCC 权限检查功能")
    print("=" * 60)
    
    from utils.permissions import check_tcc_permission
    
    tcc_permitted = check_tcc_permission()
    print(f"TCC 权限状态: {'✅ 已授权' if tcc_permitted else '❌ 未授权'}")
    
    return tcc_permitted

def test_microphone_access():
    """测试实际麦克风访问"""
    print("\n" + "=" * 60)
    print("测试实际麦克风访问")
    print("=" * 60)
    
    from utils.permissions import check_microphone_permission
    
    mic_accessible = check_microphone_permission()
    print(f"麦克风访问状态: {'✅ 可访问' if mic_accessible else '❌ 不可访问'}")
    
    return mic_accessible

def main():
    """主测试函数"""
    print("VoiceTyper 权限检查测试")
    print(f"Python 版本: {platform.python_version()}")
    print(f"操作系统: {platform.system()} {platform.release()}")
    
    if platform.system() != "Darwin":
        print("❌ 此测试仅适用于 macOS 系统")
        return
    
    # 测试各项功能
    bundle_id = test_bundle_id_detection()
    tcc_permitted = test_tcc_permission_check()
    mic_accessible = test_microphone_access()
    
    # 总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    
    if bundle_id:
        print(f"✅ Bundle ID 检测: {bundle_id}")
    else:
        print("❌ Bundle ID 检测失败")
    
    print(f"{'✅' if tcc_permitted else '❌'} TCC 权限: {'已授权' if tcc_permitted else '未授权'}")
    print(f"{'✅' if mic_accessible else '❌'} 麦克风访问: {'可访问' if mic_accessible else '不可访问'}")
    
    if mic_accessible:
        print("\n🎉 所有权限检查通过！应用可以正常使用。")
    else:
        print("\n⚠️  权限检查失败，需要手动设置权限或重新申请。")

if __name__ == "__main__":
    main() 