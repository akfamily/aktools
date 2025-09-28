# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['aktools/main.py'],
    pathex=[],
    binaries=[],
    datas=[('/python-project/aktools/venv/lib/python3.12/site-packages/akshare/file_fold', 'akshare/file_fold'), ('aktools/assets', 'aktools/assets')],
    hiddenimports=['akshare', 'uvicorn'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='aktools-web',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
