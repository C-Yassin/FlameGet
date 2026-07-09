import os
import json
import sqlite3, threading
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, Gdk, GLib, Gio

config_dir = os.path.join(GLib.get_user_config_dir(), "flameget")

themes_path = os.path.join(config_dir, "themes")
configs_path = os.path.join(config_dir, "configs") 

settings_file = os.path.join(configs_path, "settings.json")
translations_file = os.path.join(configs_path, "translations.json")

global_style_provider = None

def load_translations():
    if not os.path.exists(translations_file):
        print(f"Error: {translations_file} not found.")
        return {"en": {}}
    
    try:
        with open(translations_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
        return {"en": {}}
translations = load_translations()

def load_css(theme=""):
    display = Gdk.Display.get_default() if hasattr(Gdk, "Display") else None
    screen = Gdk.Screen.get_default() if hasattr(Gdk, "Screen") else None
    global global_style_provider
    if global_style_provider:
        try:
            if display and hasattr(Gtk.StyleContext, "remove_provider_for_display"):
                Gtk.StyleContext.remove_provider_for_display(display, global_style_provider)
            elif screen and hasattr(Gtk.StyleContext, "remove_provider_for_screen"):
                Gtk.StyleContext.remove_provider_for_screen(screen, global_style_provider)
        except Exception as e:
            print(f"CSS remove provider error: {e}")

    print(f"Switching to theme: {theme}")
    if theme == "Custom":
        css_path = os.path.join(themes_path, "custom_style.css")
    else:
        css_path = os.path.join(themes_path, f"{theme.lower()}_style.css")
    print(css_path)
    css_provider = Gtk.CssProvider()
    css_file = Gio.File.new_for_path(css_path)
    
    try:
        css_provider.load_from_file(css_file)

        if display and hasattr(Gtk.StyleContext, "add_provider_for_display"):
            Gtk.StyleContext.add_provider_for_display(
                display,
                css_provider,
                Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
            )
        elif screen and hasattr(Gtk.StyleContext, "add_provider_for_screen"):
            Gtk.StyleContext.add_provider_for_screen(
                screen,
                css_provider,
                Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
            )
        else:
            print("CSS Load Warning: No GTK display/screen available.")

        global_style_provider = css_provider
        settings = Gtk.Settings.get_default()
        if settings:
            settings.set_property("gtk-theme-name", "Adwaita")
            settings.set_property("gtk-application-prefer-dark-theme", True if theme == "Dark" else False)
        
    except Exception as e:
        print(f"CSS Load Error: {e}")

def save_settings(app_settings):
    try:
        with open(settings_file, 'w') as f:
            json.dump(app_settings, f, indent=4)
    except Exception as e:
        print(f"Failed to save settings: {e}")

def load_settings(download_folder=""):
    default_css = os.path.join(themes_path, "dark_style.css")
    custom_css = os.path.join(themes_path, "custom_style.css")
    
    home_dir = GLib.get_home_dir()
    sys_downloads = GLib.get_user_special_dir(GLib.UserDirectory.DIRECTORY_DOWNLOAD) or home_dir
    sys_videos = GLib.get_user_special_dir(GLib.UserDirectory.DIRECTORY_VIDEOS) or sys_downloads
    sys_music = GLib.get_user_special_dir(GLib.UserDirectory.DIRECTORY_MUSIC) or sys_downloads
    sys_pictures = GLib.get_user_special_dir(GLib.UserDirectory.DIRECTORY_PICTURES) or sys_downloads
    sys_documents = GLib.get_user_special_dir(GLib.UserDirectory.DIRECTORY_DOCUMENTS) or sys_downloads
    
    sys_programs = sys_downloads 

    base_dir = download_folder if download_folder else sys_downloads

    defaults = {
        "engine": "Aria2",
        "css_path": default_css,
        "custom_css_path": custom_css,
        "default_segments": 8,
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "confirm_delete": True,
        "notifications": True,
        
        "default_download_dir": base_dir,
        "video_download_dir": sys_videos,
        "music_download_dir": sys_music,
        "image_download_dir": sys_pictures,
        "program_download_dir": sys_programs,
        "document_download_dir": sys_documents,
        
        "theme_mode": "Dark",
        "language": "en",
        "max_concurrent_downloads": 8,
        "max_retries": 5,
        "font_name": "Sans Regular 11",
        "ui_scale": 100,
        "start_on_boot": False,
        "show_finish_dialog": True,
        "enable_toasts": True,
        "chk_has_borders": True,
        "enable_integration": True,
        "ctx_menu_offsets": {"x": 0, "y": 0},
        "start_in_minimize_mode": False,
        "auto_start": False,
        "global_speed_limit": "0",
        "disable_seeding": False,
        "cells_size": 1,
        "browser_port": 6812,
        "sort_column": "Date Added",
        "sort_direction": 1,
        "on_finish_action": "Do Nothing",
        "custom_finish_cmd": "",
        "shortcuts": {
            "new_download": [int(Gdk.KEY_n), int(Gdk.ModifierType.CONTROL_MASK)],
            "delete": [int(Gdk.KEY_Delete), 0],
            "select_all": [int(Gdk.KEY_a), int(Gdk.ModifierType.CONTROL_MASK)],
            "open_file": [int(Gdk.KEY_o), int(Gdk.ModifierType.CONTROL_MASK)],
            "quit": [int(Gdk.KEY_q), int(Gdk.ModifierType.CONTROL_MASK)],
            "close_window": [int(Gdk.KEY_w), int(Gdk.ModifierType.CONTROL_MASK)]
        }
    }
    
    if os.path.exists(settings_file):
        try:
            with open(settings_file, 'r') as f:
                data = json.load(f)
                
                for key, value in data.items():
                    if key in defaults and isinstance(defaults[key], dict) and isinstance(value, dict):
                        defaults[key].update(value)
                    else:
                        defaults[key] = value
        except json.JSONDecodeError as e:
            print(f"Settings file is empty or corrupted ({e}). Recreating defaults...")
            save_settings(defaults)
        except Exception as e:
            print(f"Error loading settings: {e}")
    else:
        print("Settings file not found. Creating a new one with default settings...")
        save_settings(defaults)
            
    return defaults

settings = load_settings()
def tr( text):
    lang = settings.get("language", "en")
    if lang in translations and text in translations[lang]:
        return translations[lang][text]
    return text

class DownloadDatabase:
    def __init__(self, db_name="downloads.db"):
        base_path = os.path.abspath(db_name)
        self.db_paths = {
            "main": base_path,
            "wal": f"{base_path}-wal",
            "shm": f"{base_path}-shm"
        }       
        self.conn = sqlite3.connect(db_name, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode=WAL;")
        self.conn.execute("PRAGMA synchronous=NORMAL;")
        self.conn.execute("PRAGMA busy_timeout=5000;")
        self.create_table()

    def clean_startup(self):
        def _background_clean():
            try:
                cursor = self.conn.cursor()
                cursor.execute("""
                    UPDATE downloads 
                    SET status = 'Stopped'
                    WHERE status IN ('downloading', 'Paused', 'Verifying Checksum')
                """)
                
                cursor.execute("""
                    UPDATE downloads 
                    SET status = 'Finished'
                    WHERE status = 'Seeding'
                """)
                
                self.conn.commit()
                print("Cleaned up interrupted downloads and seeds (in background).")
            except Exception as e:
                print(f"Startup cleanup failed: {e}")

        threading.Thread(target=_background_clean, daemon=True).start()

    def create_table(self):
        cursor = self.conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS downloads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT,
                size TEXT,
                status TEXT,
                progress INTEGER,
                speed TEXT,
                date_added TEXT,
                category TEXT,
                file_directory TEXT,
                url TEXT,
                pid INTEGER,
                file_size_bytes INTEGER,
                segments INT,
                is_audio BOOL,
                quality_mod TEXT,
                download_playlist BOOL,
                scheduled_time REAL DEFAULT 0,
                bandwidth_limit INT DEFAULT 0,
                priority TEXT DEFAULT 'Normal',
                finished_downloading BOOL DEFAULT False,
                hash BLOB
            )
        ''')
        
        cursor.execute("PRAGMA table_info(downloads)")
        existing_columns = [info[1] for info in cursor.fetchall()]
        
        if "priority" not in existing_columns:
            cursor.execute("ALTER TABLE downloads ADD COLUMN priority TEXT DEFAULT 'Normal'")
        if "time_left" in existing_columns:
            try: cursor.execute("ALTER TABLE downloads DROP COLUMN time_left")
            except: pass
        if "bandwidth_limit" not in existing_columns:
            cursor.execute("ALTER TABLE downloads ADD COLUMN bandwidth_limit INT DEFAULT 0")
        
        if "hash" not in existing_columns:
            cursor.execute("ALTER TABLE downloads ADD COLUMN hash BLOB")
        self.conn.commit()

    def get_downloads(self, category="All"):
        cursor = self.conn.cursor()
        if category == "All":
            cursor.execute('SELECT * FROM downloads')
        elif category == "Scheduled":
            cursor.execute('SELECT * FROM downloads WHERE status = ?', (category,))
        else:
            cursor.execute('SELECT * FROM downloads WHERE category = ?', (category,))
        return cursor.fetchall()
