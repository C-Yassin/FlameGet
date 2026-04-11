# -*- mode: python ; coding: utf-8 -*-
import os
import sys

base_datas = [
    ('flameget.png', '.'),
]
base_excludes = [
    'tkinter', 'unittest'
]

dynamic_datas = list(base_datas)
dynamic_hiddenimports = []
dynamic_excludes = list(base_excludes)
dynamic_hooksconfig = {}

if os.name == 'nt':
    dynamic_hiddenimports.extend(['pystray', 'PIL'])
    dynamic_excludes.append('gi')
else:
    dynamic_datas.extend([
        ('icons/xsi-application-exit-symbolic.svg', '.'),
        ('icons/xsi-view-reveal-symbolic.svg', '.'),
    ])
    
    dynamic_hiddenimports.extend([
        'PyQt5'
    ])
    
    dynamic_excludes.extend([
        'gi.repository.WebKit2', 'gi.repository.Gst',
        'gi.repository.GtkSource', 'gi.repository.xlib',
        'pystray', 'PIL', 'matplotlib', 'IPython', 'zmq', 'numpy',
        'PyQt6', 'PySide2', 'PySide6'
    ])
    
    dynamic_hooksconfig = {
        'gi': {
            'module-versions': {
                'Gtk': '3.0',
                'GdkPixbuf': '2.0',
                'AppIndicator3': '0.1',
                'GLib': '2.0'
            }
        }
    }

a = Analysis(
    ['tray.py'],
    pathex=[],
    binaries=[],
    datas=dynamic_datas,
    hiddenimports=dynamic_hiddenimports,
    hookspath=[],
    hooksconfig=dynamic_hooksconfig,
    runtime_hooks=[],
    excludes=dynamic_excludes,
    noarchive=False,
    optimize=2,
)

pyz = PYZ(a.pure)

if os.name != 'nt':
    filtered_datas = []
    for data in a.datas:
        dest_path = data[0]
        if dest_path.startswith('share') or dest_path.startswith(r'share\\'):
            if 'glib-2.0' in dest_path and 'schemas' in dest_path:
                filtered_datas.append(data)
            else:
                pass
        else:
            filtered_datas.append(data)
    a.datas = filtered_datas

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='tray',
    debug=False,
    bootloader_ignore_signals=False,
    strip=True,
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