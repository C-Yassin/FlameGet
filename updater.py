import urllib.request
import json
import os
import webbrowser
import platform
import threading
import io
import zipfile

import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, GLib

FLAMEGET_VERSION = "v1.2"
REPO = "C-Yassin/FlameGet"
API_URL = f"https://api.github.com/repos/{REPO}/releases/latest"

class UpdaterLogic:
    @staticmethod
    def get_install_type():
        if os.path.exists("/.flatpak-info"):
            return "flatpak"
            
        if os.environ.get('APPIMAGE'):
            return "appimage"
            
        if os.path.exists("/usr/bin/flameget") or os.path.exists("/usr/share/flameget"):
            if os.path.exists("/etc/arch-release"):
                return "aur"
            return "deb"
            
        if platform.system() == "Windows":
            return "windows"
        
        return "portable"

class UpdaterWindow(Gtk.ApplicationWindow):
    def __init__(self, *args, **kwargs):
        self.is_hidden = kwargs.pop('is_hidden', False)
        
        super().__init__(*args, **kwargs)
        self.set_title("FlameGet Updater")
        self.set_default_size(350, -1)

        self.install_mode = UpdaterLogic.get_install_type()
        self.latest_version = None
        self.download_url = None
        self.release_url = None

        self.box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)
        self.box.set_margin_top(20)
        self.box.set_margin_bottom(20)
        self.box.set_margin_start(20)
        self.box.set_margin_end(20)
        self.set_child(self.box)

        self.status_label = Gtk.Label(label=f"Current version: {FLAMEGET_VERSION}\nMode: {self.install_mode.upper()}")
        self.status_label.set_justify(Gtk.Justification.CENTER)
        self.box.append(self.status_label)

        if not self.is_hidden:
            self.check_button = Gtk.Button(label="Check for Updates")
            self.check_button.connect("clicked", self.on_check_clicked)
            self.box.append(self.check_button)

        self.action_button = Gtk.Button(label="Update")
        self.action_button.connect("clicked", self.on_action_clicked)
        self.action_button.set_visible(False)
        self.box.append(self.action_button)

    def on_check_clicked(self, button):
        if not self.is_hidden: self.check_button.set_sensitive(False)
        self.status_label.set_text("Checking GitHub for updates...")
        threading.Thread(target=self.fetch_version, daemon=True).start()

    def fetch_version(self):
        try:
            req = urllib.request.Request(API_URL, headers={'User-Agent': 'FlameGet-Updater'})
            with urllib.request.urlopen(req) as response:
                data = json.loads(response.read().decode('utf-8'))
                
                self.latest_version = data.get("tag_name")
                self.download_url = data.get("zipball_url")
                self.release_url = data.get("html_url")

                if self.latest_version and self.latest_version != FLAMEGET_VERSION:
                    GLib.idle_add(self.show_update_available)
                else:
                    GLib.idle_add(self.show_up_to_date)
        except Exception as e:
            GLib.idle_add(self.show_error, str(e))

    def show_update_available(self):
        self.status_label.set_text(f"Update found: {self.latest_version}!")
        if not self.is_hidden: self.check_button.set_sensitive(True)
        
        if self.install_mode == "aur":
            self.action_button.set_label("How to update (AUR)")
        elif self.install_mode == "flatpak":
            self.action_button.set_label("How to update (Flatpak)")
        elif self.install_mode in ["deb", "appimage", "windows"]:
            self.action_button.set_label(f"Download {self.latest_version} via Browser")
        else:
            self.action_button.set_label("Auto-Download & Apply")

        self.action_button.set_visible(True)

    def show_up_to_date(self):
        self.status_label.set_text("You are already on the latest version!")
        if not self.is_hidden: self.check_button.set_sensitive(True)
        self.action_button.set_visible(False)

    def show_error(self, error_msg):
        self.status_label.set_text(f"Network Error:\n{error_msg}")
        if not self.is_hidden: self.check_button.set_sensitive(True)

    def on_action_clicked(self, button):
        if self.install_mode == "portable":
            self.action_button.set_sensitive(False)
            if not self.is_hidden: self.check_button.set_sensitive(False)
            self.status_label.set_text("Downloading and extracting...\n(Do not close this window)")
            threading.Thread(target=self.download_and_apply_portable, daemon=True).start()
            
        elif self.install_mode == "flatpak":
            self.status_label.set_text("Please open your Software Center\nor run 'flatpak update' in your terminal.")
            self.action_button.set_sensitive(False)
            
        elif self.install_mode == "aur":
            self.status_label.set_text("Please run 'yay -Syu' (or your AUR helper)\nin your terminal to update.")
            self.action_button.set_sensitive(False)
            
        else:
            webbrowser.open(self.release_url)
            self.status_label.set_text("Opened browser for download.")

    def download_and_apply_portable(self):
        try:
            req = urllib.request.Request(self.download_url, headers={'User-Agent': 'FlameGet-Updater'})
            with urllib.request.urlopen(req) as response:
                zip_data = io.BytesIO(response.read())
                
                with zipfile.ZipFile(zip_data) as zip_ref:
                    for member in zip_ref.namelist():
                        if not os.path.basename(member):
                            continue
                        
                        path_parts = member.split('/')[1:] 
                        if not path_parts: continue
                        
                        target_path = os.path.join(os.getcwd(), *path_parts)
                        os.makedirs(os.path.dirname(target_path), exist_ok=True)
                        
                        with zip_ref.open(member) as source, open(target_path, "wb") as target:
                            target.write(source.read())
                            
            GLib.idle_add(self.show_update_success)
        except Exception as e:
            GLib.idle_add(self.show_error, str(e))

    def show_update_success(self):
        self.status_label.set_text(f"Update to {self.latest_version} successful!\nPlease restart the application.")
        self.action_button.set_visible(False)
        if not self.is_hidden: self.check_button.set_visible(False)


class SilentUpdater:
    def __init__(self, application=None, is_hidden=False):
        self.app = application
        self.window = None
        self.is_hidden = is_hidden

    def check_silently(self):
        """Spawns the background thread."""
        threading.Thread(target=self._fetch_and_compare, daemon=True).start()

    def _fetch_and_compare(self):
        try:
            req = urllib.request.Request(API_URL, headers={'User-Agent': 'FlameGet-Updater'})
            with urllib.request.urlopen(req) as response:
                data = json.loads(response.read().decode('utf-8'))
                latest_version = data.get("tag_name")

                if latest_version and latest_version != FLAMEGET_VERSION:
                    print(f"Update found: {latest_version}. Popping up...")
                    GLib.idle_add(self.show_updater_window)
                else:
                    print("No update found.")
        except Exception as e:
            print(f"Silent check failed: {e}")

    def show_updater_window(self):
        if not self.window:
            if self.app:
                self.window = UpdaterWindow(application=self.app, is_hidden=self.is_hidden)
            else:
                self.window = UpdaterWindow()
                
        self.window.present()
        self.window.fetch_version()