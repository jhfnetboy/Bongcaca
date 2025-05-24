# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all

datas = [('resources', 'resources')]
binaries = []
hiddenimports = ['faster_whisper', 'PySide6.QtCore', 'PySide6.QtWidgets', 'PySide6.QtGui', 'pyaudio', 'numpy', 'logging', 'tempfile', 'threading', 'pathlib', 'subprocess', 'platform', 'psutil', 'huggingface_hub', 'Quartz', 'ui.floating_window', 'ui.logo', 'ui.macos_app_icon', 'core.engine', 'core.recorder', 'core.hotkey_listener', 'utils.config', 'utils.logging', 'platform_specific.input']
tmp_ret = collect_all('faster_whisper')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('pyaudio')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]


a = Analysis(
    ['launcher.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['matplotlib', 'PyQt5', 'PyQt6', 'tkinter'],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [('v', None, 'OPTION')],
    exclude_binaries=True,
    name='VoiceTyper',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['resources/icons/app_icon.icns'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='VoiceTyper',
)
app = BUNDLE(
    coll,
    name='VoiceTyper.app',
    icon='resources/icons/app_icon.icns',
    bundle_identifier='com.bongcaca.voicetyper',
)
