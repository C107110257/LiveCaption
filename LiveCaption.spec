# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('C:/Users/PC-103/AppData/Local/Programs/Python/Python312/Lib/site-packages/faster_whisper/assets', 'faster_whisper/assets')],
    hiddenimports=['faster_whisper', 'ctranslate2', 'transformers'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['pandas', 'scipy', 'matplotlib', 'IPython', 'jupyter', 'tensorflow', 'tensorboard', 'sklearn', 'PIL', 'cv2', 'notebook', 'sphinx', 'safetensors', 'rich', 'typer', 'click', 'jinja2'],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='LiveCaption',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='LiveCaption',
)
