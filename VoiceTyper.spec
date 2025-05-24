# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('resources/icons', 'resources/icons')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['matplotlib', 'notebook', 'PIL.ImageQt', 'PyQt5', 'PyQt6', 'tkinter', 'scipy', 'pandas', 'IPython', 'jupyter', 'nbconvert', 'nbformat', 'ipykernel', 'ipywidgets', 'traitlets', 'tornado', 'jedi', 'parso', 'pygments', 'sphinx', 'docutils', 'nose', 'pytest', 'unittest', 'xml', 'email', 'html', 'http', 'distutils', 'pkg_resources', 'setuptools', 'pydoc'],
    noarchive=False,
    optimize=1,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [('O', None, 'OPTION')],
    name='VoiceTyper',
    debug=False,
    bootloader_ignore_signals=False,
    strip=True,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['resources/icons/app_icon.icns'],
)
app = BUNDLE(
    exe,
    name='VoiceTyper.app',
    icon='resources/icons/app_icon.icns',
    bundle_identifier='com.bongcaca.voicetyper',
)
