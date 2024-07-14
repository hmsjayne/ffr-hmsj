# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.building.build_main import Analysis

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