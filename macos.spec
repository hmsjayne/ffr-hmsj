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
    [],
    exclude_binaries=True,
    name='randomize',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch="universal2",
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
    name='Final Fantasy HMS Jayne',
)
app = BUNDLE(
    coll,
    name="Final Fantasy HMS Jayne.app",
    icon="static/hms-jayne.icns",
    bundle_identifier="com.hmsjayne.macos",
)
