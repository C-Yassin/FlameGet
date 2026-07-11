@echo off

call "C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvars64.bat"

python -m nuitka ^
  --standalone ^
  --onefile ^
  --windows-icon-from-ico=../icons/icon.ico ^
  --company-name="C-Yassin" ^
  --product-name="FlameGet" ^
  --file-version=1.5 ^
  --file-description="FlameGet's tray system" ^
  --copyright="MIT 2026" ^
  --windows-console-mode=disable ^
  --enable-plugin=gi ^
  --python-flag=-OO ^
  --include-data-files="../icons/flameget.png=icons/flameget.png" ^
  --include-data-files="../icons/xsi-window-close-symbolic.svg=icons/xsi-window-close-symbolic.svg" ^
  --include-data-files="../icons/xsi-view-reveal-symbolic.svg=icons/xsi-view-reveal-symbolic.svg" ^
  --nofollow-import-to=gi.repository.WebKit2 ^
  --nofollow-import-to=gi.repository.Gst ^
  --nofollow-import-to=gi.repository.GtkSource ^
  --nofollow-import-to=gi.repository.xlib ^
  --nofollow-import-to=tkinter ^
  --nofollow-import-to=unittest ^
  --nofollow-import-to=pydoc ^
  --nofollow-import-to=xml ^
  --nofollow-import-to=email ^
  --nofollow-import-to=http ^
  --nofollow-import-to=urllib ^
  --nofollow-import-to=html ^
  --nofollow-import-to=bz2 ^
  --nofollow-import-to=lzma ^
  --nofollow-import-to=matplotlib ^
  --nofollow-import-to=IPython ^
  --nofollow-import-to=zmq ^
  --nofollow-import-to=numpy ^
  --nofollow-import-to=PyQt5 ^
  --nofollow-import-to=PyQt6 ^
  --nofollow-import-to=PySide2 ^
  --nofollow-import-to=PySide6 ^
  ../tray.py
pause