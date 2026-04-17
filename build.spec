# -*- mode: python ; coding: utf-8 -*-

from argparse import ArgumentParser
from platform import system
import shutil, os, stat, sys

parser = ArgumentParser()
parser.add_argument("--binary", action="store_true")
options = parser.parse_args()
# Automatically grabs "3.12", "3.13", "3.14" tsk >:(
py_version = f"python{sys.version_info.major}.{sys.version_info.minor}"

actual_packages_path = os.path.abspath(f'venv/lib/{py_version}/site-packages')
dynamic_hidden_imports = [
    'Toast',
    'browser_context_menu_handler',
    'downloader',
    'SaveManager',
    'FireAddOns',
    'flask',
    'waitress',
    'yt_dlp',
    'aria2p',
    'pycurl',
    'gi',
    'psutil',
    'yt_dlp.utils',
    'aria2p.client',
    'aria2p.api',
]

if os.name == 'nt':
    dynamic_hidden_imports.append('winotify')
    dynamic_hidden_imports.append('pystray')

dynamic_binaries = []
if os.name == 'nt':
    dynamic_binaries.append(('binaries/aria2c.exe', 'binaries'))
    dynamic_binaries.append(('binaries/tray.exe', 'binaries'))
else:
    dynamic_binaries.append(('binaries/tray.bin', 'binaries'))

a = Analysis(
    ['main.py'],
    pathex=[actual_packages_path, '.'],
    binaries=dynamic_binaries,
    datas=[
        ('LICENSE', '.'),
        ('*.css', '.'),
        ('icons', 'icons'),
        ("*.json", '.')
    ],
    hiddenimports=dynamic_hidden_imports,
    hookspath=[],
    hooksconfig={
        'gi': {
            'module-versions': {
                'Gtk': '4.0'
            }
        }
    },
    runtime_hooks=[],
    excludes=[
        'setuptools', 
        'pkg_resources', 
        'tkinter',
        'unittest'
        'yt_dlp.extractor.lazy_extractors'
    ],
    noarchive=False,
)
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
pyz = PYZ(a.pure)

if system() == "Linux":
    if not options.binary:
        exe = EXE(
            pyz,
            a.scripts,
            [],
            exclude_binaries=True,
            name='FlameGet',
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
        )
        coll = COLLECT(
            exe,
            a.binaries,
            a.datas,
            strip=False,
            upx=True,
            upx_exclude=[],
            name='FlameGet',
        )
    else:
        exe = EXE(
            pyz,
            a.scripts,
            a.binaries,
            a.datas,
            [],
            name='FlameGet',
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
elif system() == "Darwin": # macOS
    if not options.binary:
        exe = EXE(
            pyz,
            a.scripts,
            [],
            exclude_binaries=True,
            name='FlameGet',
            icon='icon.icns', # <-- Updated Mac icon name
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
        )
        coll = COLLECT(
            exe,
            a.binaries,
            a.datas,
            strip=False,
            upx=True,
            upx_exclude=[],
            name='FlameGet',
        )
        app = BUNDLE(
            coll,
            name='FlameGet.app',
            icon='icon.icns',
            bundle_identifier=None,
            version=None,
        )
    else:
        exe = EXE(
            pyz,
            a.scripts,
            a.binaries,
            a.datas,
            [],
            name='FlameGet',
            icon='icon.icns',
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
elif system() == "Windows":
    if not options.binary:
        exe = EXE(
            pyz,
            a.scripts,
            [],
            exclude_binaries=True,
            name='FlameGet',
            icon='icon.ico',
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
        )
        coll = COLLECT(
            exe,
            a.binaries,
            a.datas,
            strip=False,
            upx=True,
            upx_exclude=[],
            name='FlameGet',
        )
    else:
        exe = EXE(
            pyz,
            a.scripts,
            a.binaries,
            a.datas,
            [],
            name='FlameGet',
            icon='icon.ico',
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

def force_delete(func, path, excinfo):
    os.chmod(path, stat.S_IWRITE)
    func(path)

app_folder = os.path.join(DISTPATH, 'FlameGet')
internal_folder = os.path.join(app_folder, '_internal') 

source_icons = os.path.abspath(os.path.join(SPECPATH, 'icons'))
target_icons = os.path.abspath(os.path.join(app_folder, 'icons'))
internal_icons = os.path.abspath(os.path.join(internal_folder, 'icons'))

source_binaries = os.path.abspath(os.path.join(SPECPATH, 'binaries'))
target_binaries = os.path.abspath(os.path.join(app_folder, 'binaries'))
internal_binaries = os.path.abspath(os.path.join(internal_folder, 'binaries'))

if os.path.exists(source_icons):
    if source_icons != target_icons:
        if os.path.exists(target_icons):
            shutil.rmtree(target_icons, onerror=force_delete)
            
        shutil.copytree(source_icons, target_icons)
        
        if os.path.exists(internal_icons):
            shutil.rmtree(internal_icons, onerror=force_delete)

if os.path.exists(source_binaries):
    if source_binaries != target_binaries:
        if os.path.exists(target_binaries):
            shutil.rmtree(target_binaries, onerror=force_delete)
            
        shutil.copytree(source_binaries, target_binaries)
        
        if os.path.exists(internal_binaries):
            shutil.rmtree(internal_binaries, onerror=force_delete)
