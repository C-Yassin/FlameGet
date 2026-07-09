import importlib, sys, re, os
import shutil, psutil, filecmp, json, socket, subprocess, time, random, atexit

import gi
gi.require_version('Gtk', '4.0')
from gi.repository import GLib, Gtk, Gdk

def lazy_import(name):
    spec = importlib.util.find_spec(name)
    if spec is None or spec.loader is None:
        raise ImportError(f"Module '{name}' could not be found for lazy import.")
    loader = importlib.util.LazyLoader(spec.loader)
    spec.loader = loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    loader.exec_module(module)
    return module

class _FileManager():
    def __init__(self):
        if os.name == 'nt':
            base_config = os.getenv('APPDATA', os.path.expanduser('~'))
            base_data = os.getenv('LOCALAPPDATA', base_config)
            self.config_dir = os.path.join(base_data, "flameget")
            self.data_dir = os.path.join(base_data, "flameget")
        else:
            self.config_dir = os.path.join(GLib.get_user_config_dir(), "flameget")
            self.data_dir = os.path.join(GLib.get_user_data_dir(), "flameget")

        os.makedirs(self.config_dir, exist_ok=True)
        os.makedirs(self.data_dir, exist_ok=True)
        
        self.is_compiled = getattr(sys, 'frozen', False) or "__compiled__" in globals()
        
        if self.is_compiled:
            self.current_exe = sys.executable
            self.install_dir = os.path.dirname(self.current_exe)
            ext = ""
        else:
            self.current_exe = sys.executable
            self.install_dir = os.path.dirname(os.path.abspath(__file__))
            ext = ".py"

        self.downloader_script_path = os.path.join(self.install_dir, f"downloader{ext}")
        self.browser_context_menu_handler_script_path = os.path.join(self.install_dir, f"browser_context_menu_handler{ext}")
        self.server_script_path = os.path.join(self.install_dir, f"server{ext}")
        self.binaries_path = os.path.join(self.install_dir, "binaries")
        self.themes_path = os.path.join(self.install_dir, "themes")
        self.configs_path = os.path.join(self.install_dir, "configs")

        if self.is_compiled:
            self.tray_script_path = os.path.join(self.binaries_path,  "tray.exe" if os.name =="nt" else "tray.bin")
        else:
            self.tray_script_path = os.path.join(self.install_dir, "tray.py")

        self.aria2c_path = "aria2c" if os.name != "nt" else os.path.join(self.binaries_path, "aria2c.exe")
        
        self.rustypipe_botguard_path = os.path.join(self.binaries_path, f'rustypipe-botguard{".exe" if os.name == "nt" else ""}')
        os.environ["PATH"] = os.path.abspath(self.binaries_path) + os.pathsep + os.environ.get("PATH", "")
        self.icons_dir = os.path.join(self.install_dir, "icons")
        self.ffmpeg_path = os.path.join(self.binaries_path, "ffmpeg.exe") if os.name == "nt" else shutil.which("ffmpeg")
        display = Gdk.Display.get_default()
        icon_theme = Gtk.IconTheme.get_for_display(display)
        icon_theme.add_search_path(self.icons_dir)
        
        self.setup_settings()

        self.db_file = os.path.join(self.data_dir, "downloads.db")
        self.db = self.create_db()
        
    def create_db(self):
        from SaveManager import DownloadDatabase
        return DownloadDatabase(db_name=self.db_file)
    
    def setup_settings(self):
        internal_node = ("_internal",) if getattr(self, 'is_compiled', False) else ()
        system_themes = os.path.join(self.install_dir, *internal_node, "themes")
        system_configs = os.path.join(self.install_dir, *internal_node, "configs")
        
        user_themes = os.path.join(self.config_dir, "themes")
        user_configs = os.path.join(self.config_dir, "configs")

        os.makedirs(user_themes, exist_ok=True)
        os.makedirs(user_configs, exist_ok=True)

        def copy_missing_files(src_dir, dst_dir):
            if not os.path.exists(src_dir):
                return
            for item in os.listdir(src_dir):
                s_item = os.path.join(src_dir, item)
                d_item = os.path.join(dst_dir, item)
                
                if os.path.isdir(s_item):
                    os.makedirs(d_item, exist_ok=True)
                    copy_missing_files(s_item, d_item)
                elif not os.path.exists(d_item):
                    try:
                        shutil.copy2(s_item, d_item)
                        print(f"Copied missing file: {item}")
                    except Exception as e:
                        print(f"Failed to copy missing file {item}: {e}")

        copy_missing_files(system_themes, user_themes)
        copy_missing_files(system_configs, user_configs)

        for css_file in ["dark_style.css", "light_style.css"]:
            sys_css = os.path.join(system_themes, css_file)
            user_css = os.path.join(user_themes, css_file)
            
            if os.path.exists(sys_css) and os.path.exists(user_css):
                if not filecmp.cmp(sys_css, user_css, shallow=False):
                    try:
                        shutil.copy2(sys_css, user_css)
                        print(f"Updated {css_file}")
                    except Exception as e:
                        print(f"Failed to update {css_file}: {e}")

        sys_trans = os.path.join(system_configs, "translations.json")
        user_trans = os.path.join(user_configs, "translations.json")
        
        if os.path.exists(sys_trans) and os.path.exists(user_trans):
            if not filecmp.cmp(sys_trans, user_trans, shallow=False):
                try:
                    with open(sys_trans, 'r', encoding='utf-8-sig') as sf:
                        system_data = json.load(sf)
                    with open(user_trans, 'r', encoding='utf-8-sig') as uf:
                        try:
                            user_data = json.load(uf)
                        except json.JSONDecodeError:
                            user_data = {}
                    
                    def sync_dicts(default_dict, user_dict):
                        has_changes = False
                        for k, v in default_dict.items():
                            if k not in user_dict:
                                user_dict[k] = v
                                has_changes = True
                            elif isinstance(v, dict) and isinstance(user_dict[k], dict):
                                if sync_dicts(v, user_dict[k]):
                                    has_changes = True
                                    
                        keys_to_remove = [k for k in list(user_dict.keys()) if k not in default_dict]
                        for k in keys_to_remove:
                            del user_dict[k]
                            has_changes = True
                            
                        return has_changes

                    if sync_dicts(system_data, user_data):
                        with open(user_trans, 'w', encoding='utf-8', newline='') as uf:
                            json.dump(user_data, uf, indent=4, ensure_ascii=False)
                        print("Successfully merged translations.json")
                        
                except Exception as e:
                    print(f"Failed to merge translations.json: {e}")

FireFiles = _FileManager()

class UNITS():
    def get_temp_dir():
        if os.name == 'nt':
            base_data = os.getenv('LOCALAPPDATA', os.path.expanduser('~'))
            RUNTIME_DIR = os.path.join(base_data, "flameget", "run")
            os.makedirs(RUNTIME_DIR, exist_ok=True)
            return RUNTIME_DIR
        else:
            return os.environ.get("XDG_RUNTIME_DIR", "/tmp")
        
    SIZE_RE = re.compile(r"/([0-9.]+)([KMG]i?)B", re.I)
    
    RUNTIME_DIR = get_temp_dir()
    MULT = {
        "b": 1, "byte": 1, "bytes": 1,

        "k": 1000, "kb": 1000, 
        "ki": 1024, "kib": 1024,

        "m": 1000**2, "mb": 1000**2, 
        "mi": 1024**2, "mib": 1024**2,

        "g": 1000**3, "gb": 1000**3, 
        "gi": 1024**3, "gib": 1024**3,

        "t": 1000**4, "tb": 1000**4, 
        "ti": 1024**4, "tib": 1024**4,

        # WHO THE FUCK HAS THIS AMOUNT OF DATA DAYUUM
        "p": 1000**5, "pb": 1000**5, 
        "pi": 1024**5, "pib": 1024**5,
    }
    COMPRESSED = {
        ".zip", ".rar", ".7z", ".tar", ".gz", ".bz2", ".xz",
        ".tgz", ".tbz2", ".txz", ".zst", ".iso"
    }
    PROGRAMS = {
        ".exe", ".msi", ".apk", ".appimage", ".deb", ".rpm",
        ".run", ".bin", ".sh"
    }
    VIDEOS = {
        ".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv",
        ".webm", ".mpeg", ".mpg", ".m4v"
    }
    MUSIC = {
        ".mp3", ".flac", ".wav", ".ogg", ".aac", ".m4a",
        ".opus", ".wma"
    }
    PICTURES = {
        ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp",
        ".tiff", ".svg", ".avif"
    }
    DOCUMENTS = {
        ".pdf", ".doc", ".docx", ".odt", ".rtf", ".txt",
        ".md", ".ppt", ".pptx", ".xls", ".xlsx", ".ods",
        ".csv", ".epub"
    }
    SUPPORTED_SITES = {
        "youtube.com", "youtu.be",
        "twitch.tv", "tiktok.com",
        "instagram.com", "facebook.com", "fb.watch",
        "twitter.com", "x.com",
        "vimeo.com", "dailymotion.com",
        "soundcloud.com", "mixcloud.com",
        "reddit.com", "pinterest.com",
        "bilibili.com", "vk.com", 
        "odysee.com", "rumble.com",
        "streamable.com"
    }


def categorize_filename(filename, is_torrent=False):
    ext = os.path.splitext(filename.lower())[1]
    if is_torrent:
        return "Torrent"
    if ext in UNITS.COMPRESSED:
        return "Compressed"
    if ext in UNITS.PROGRAMS:
        return "Programs"
    if ext in UNITS.VIDEOS:
        return "Videos"
    if ext in UNITS.MUSIC:
        return "Music"
    if ext in UNITS.PICTURES:
        return "Pictures"
    if ext in UNITS.DOCUMENTS:
        return "Documents"

    return "Documents"

def _delete_active_part_worker(filename, directory):
    base_name = os.path.splitext(filename)[0]
    suffix_pattern = re.compile(r"\.(part|ytdl)(-Frag\d+)?(\.part)?$")    
    
    active_files = []
    for name in os.listdir(directory):
        if name.startswith(base_name) and suffix_pattern.search(name):
            active_files.append(os.path.join(directory, name))
            
    if not active_files:
        print("got NONE!")
        return None

    print(f"got {active_files}")
    active_files.append(os.path.join(directory, filename))
    deleted_count = 0
    for file_to_delete in active_files:
        try:
            os.remove(file_to_delete)
            deleted_count += 1
        except OSError:
            pass

def check_and_fix_filename(db, directory, name_to_check):
    cursor = db.conn.cursor()
    def exists_in_db(test_name):
        cursor.execute(
            "SELECT 1 FROM downloads WHERE filename = ? AND file_directory = ?", 
            (test_name, directory)
        )
        return cursor.fetchone() is not None

    if not exists_in_db(name_to_check):
        return name_to_check

    base_name, ext = os.path.splitext(name_to_check)
    new_name = name_to_check
    counter = 1

    while exists_in_db(new_name):
        print(f"'{new_name}' already exists in the database! Trying next number...")
        new_name = f"{base_name}({counter}){ext}"
        counter += 1

    return new_name

def get_progress_from_db(db, directory, filename):
    cursor = db.conn.cursor()
    cursor.execute(
        "SELECT progress FROM downloads WHERE filename = ? AND file_directory = ?", 
        (filename, directory)
    )
    result = cursor.fetchone()

    if result is not None:
        return result["progress"] 
    else:
        return 0

def find_active_part_yt_dlp(filename, directory):
    base_name = os.path.splitext(filename)[0]
    for name in os.listdir(directory):
        if name.startswith(base_name) and (name.endswith(".part") or name.endswith(".ytdl")):
            return os.path.join(directory, name)
    return None

#for the downloader
def parse_size(file_size_in_bytes):
    return (
        f"{file_size_in_bytes} B" if file_size_in_bytes < 1024 else
        f"{file_size_in_bytes / 1024:.2f} KB" if file_size_in_bytes < 1024**2 else
        f"{file_size_in_bytes / (1024 ** 2):.2f} MB" if file_size_in_bytes < 1024**3 else
        f"{file_size_in_bytes / (1024 ** 3):.2f} GB" if file_size_in_bytes < 1024**4 else
        f"{file_size_in_bytes / (1024 ** 4):.2f} TB"
    )

def range_parse_size(val, unit):
    unit = unit.lower()
    if not unit.endswith("b"):
        unit += "b"

    return int(float(val) * UNITS.MULT[unit])

def is_pid_alive(pid: int) -> bool:
    return psutil.pid_exists(pid)

def is_valid_url(text):
    text = text.strip()
    if not text:
        return False
        
    if text.lower().startswith("magnet:?") or text.lower().endswith(".torrent"):
        return True
        
    pattern = re.compile(
        r'^(?:(?:https?|ftp)://)?'
        r'(?:[\w-]+\.)+[a-z]{2,}'
        r'(?:/\S*)?$',
        re.IGNORECASE
    )
    
    return bool(pattern.match(text))

def set_titlebar_theme(window_title, theme_str="Dark"):
    if os.name != 'nt':
        return
    
    import ctypes    
    try:
        hwnd = ctypes.windll.user32.FindWindowW(None, window_title)
        
        if hwnd:
            DWMWA_USE_IMMERSIVE_DARK_MODE = 20
            
            # If dark_mode is True, send 1. If False, send 0.
            dark_mode = 1 if theme_str == "Dark" else 0
            set_theme = ctypes.c_int(dark_mode)
            
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd,
                DWMWA_USE_IMMERSIVE_DARK_MODE,
                ctypes.byref(set_theme),
                ctypes.sizeof(set_theme)
            )
            print(f"Successfully set Windows title bar to {theme_str} mode.")
        else:
            print("Could not find window to apply title bar theme.")
            
    except Exception as e:
        print(f"DWM API failed: {e}")


import os
import ctypes
from ctypes import wintypes

def force_center_dialog(dialog_title, parent_title=None):
    if os.name != 'nt':
        return False 

    user32 = ctypes.windll.user32
    
    user32.FindWindowW.restype = wintypes.HWND
    user32.FindWindowW.argtypes = [wintypes.LPCWSTR, wintypes.LPCWSTR]
    
    user32.GetWindowRect.restype = wintypes.BOOL
    user32.GetWindowRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]
    
    user32.SetWindowPos.restype = wintypes.BOOL
    user32.SetWindowPos.argtypes = [wintypes.HWND, wintypes.HWND, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_uint]

    hwnd_dialog = user32.FindWindowW(None, dialog_title)
    if not hwnd_dialog:
        print(f"DEBUG: Could not find window with title '{dialog_title}'")
        return False
        
    rect_dlg = wintypes.RECT()
    user32.GetWindowRect(hwnd_dialog, ctypes.byref(rect_dlg))
    dlg_width = rect_dlg.right - rect_dlg.left
    dlg_height = rect_dlg.bottom - rect_dlg.top
    
    hwnd_main = user32.FindWindowW(None, parent_title) if parent_title else None
    
    if hwnd_main:
        rect_main = wintypes.RECT()
        user32.GetWindowRect(hwnd_main, ctypes.byref(rect_main))
        main_width = rect_main.right - rect_main.left
        main_height = rect_main.bottom - rect_main.top
        
        x = rect_main.left + (main_width - dlg_width) // 2
        y = rect_main.top + (main_height - dlg_height) // 2
    else:
        SM_CXSCREEN = 0
        SM_CYSCREEN = 1
        screen_width = user32.GetSystemMetrics(SM_CXSCREEN)
        screen_height = user32.GetSystemMetrics(SM_CYSCREEN)
        
        x = (screen_width - dlg_width) // 2
        y = (screen_height - dlg_height) // 2
        
    HWND_TOPMOST = ctypes.c_void_p(-1)
    SWP_NOSIZE = 0x0001
    
    user32.SetWindowPos(hwnd_dialog, HWND_TOPMOST, x, y, 0, 0, SWP_NOSIZE)
    
    return False


class Aria2DaemonManager:
    def __init__(self, aria2c_path, app_settings):
        self.ARIA_PORT = 6822
        self.aria2c_path = aria2c_path
        self.proc = None
        self.app_settings = app_settings
        
        if not self.is_port_free(self.ARIA_PORT):
            self.get_random_port()

    def get_random_port(self):
        while True:
            candidate = random.randint(7000, 9001)
            if self.is_port_free(candidate):
                self.ARIA_PORT = candidate
                break

    def is_port_free(self, port):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(('127.0.0.1', port))
                return True
            except OSError:
                return False

    def start(self):
        master_secret = os.urandom(16).hex()
        os.environ["FLAMEGET_ARIA_PORT"] = str(self.ARIA_PORT)
        os.environ["FLAMEGET_ARIA_SECRET"] = master_secret

        cmd = [
            self.aria2c_path,
            "--enable-rpc=true",
            f"--rpc-listen-port={self.ARIA_PORT}",
            "--rpc-allow-origin-all=true",
            "--rpc-listen-all=false",
            f"--max-concurrent-downloads={self.app_settings.get("max_concurrent_downloads")}",
            "--continue=true",
            "--file-allocation=none",
            "--min-split-size=1M",
            f"--max-tries={self.app_settings.get("max_retries")}",
            "--retry-wait=3"
        ]

        def _daemon():
            try:
                self.proc = subprocess.Popen(
                    cmd,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    **({"creationflags": subprocess.CREATE_NO_WINDOW} if os.name == "nt" else {})
                )

                time.sleep(1.0)

                if self.proc.poll() is not None:
                    print(f"CRITICAL: Aria2c crashed instantly with exit code {self.proc.poll()}")
                else:
                    print(f"Aria2 Master Daemon successfully registered on {self.ARIA_PORT}!")
                    atexit.register(self.stop)
                    
            except Exception as e:
                print(f"Daemon launch failed: {e}")
        
        import threading
        threading.Thread(target=_daemon, daemon=True).start()

    def stop(self):
        if self.proc: self.proc.terminate()
