# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['randomize-gui.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('asp/*', 'asp'),
        ('data/*', 'data'),
        ('patches/*.ips', 'patches'),
        ('scripts/*', 'scripts'),
        ('static/*', 'static'),
    ],
    hiddenimports=['clingo._internal', 'cffi'],
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
    name='Final Fantasy HMS Jayne',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
app = BUNDLE(
    exe,
    name='Final Fantasy HMS Jayne.app',
    icon="icons/hms-jayne.ico",
    bundle_identifier="com.hmsjayne.app",
)
