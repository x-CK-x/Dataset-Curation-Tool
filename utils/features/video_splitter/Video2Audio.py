import os
import subprocess
import sys
import platform
import gradio as gr

from utils import helper_functions as help

try:
    import tkinter as tk
    from tkinter.simpledialog import askstring
except ImportError:
    tk = None

class Video2Audio:
    def _is_tool_installed(self, name):
        """Check whether a given tool is installed."""
        try:
            subprocess.run([name], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return True
        except FileNotFoundError:
            return False

    def _get_linux_password(self):
        """Get sudo password using tkinter pop-up."""
        if tk is None:
            help.verbose_print("Please ensure you have tkinter installed to use this feature.")

        root = tk.Tk()
        root.withdraw()  # Hide the main window
        password = askstring("Password Input", "Please enter your sudo password:", show='*')
        return password

    def _install_ffmpeg(self):
        """Install ffmpeg based on the operating system."""
        if self.os_name == "Linux":
            password = self._get_linux_password()
            command1 = ["sudo", "-S", "apt-get", "update"]
            command2 = ["sudo", "-S", "apt-get", "install", "-y", "ffmpeg"]

            proc1 = subprocess.Popen(command1, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
            proc2 = subprocess.Popen(command2, stdin=subprocess.PIPE, stderr=subprocess.PIPE)

            proc1.communicate(password.encode() + b'\n')
            proc2.communicate(password.encode() + b'\n')

        elif self.os_name == "Darwin":  # macOS
            subprocess.run(["brew", "install", "ffmpeg"], check=True)
        elif self.os_name == "Windows":
            help.verbose_print("Please install ffmpeg manually from https://ffmpeg.org/download.html.")
        else:
            help.verbose_print("Unsupported OS. Please install ffmpeg manually.")

    def extract_audio(self, video_path, output_path=None):
        self.os_name = platform.system()
        if not self._is_tool_installed("ffmpeg"):
            help.verbose_print("ffmpeg is not installed. Attempting to install...")
            self._install_ffmpeg()

        """Extract audio from a video file using ffmpeg."""
        if output_path is None:
            output_path = os.path.splitext(video_path)[0] + ".mp3"

        cmd = ["ffmpeg", "-i", video_path, "-q:a", "0", "-map", "a", output_path]

        try:
            subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return gr.update(value=output_path)
        except Exception as e:
            help.verbose_print(f"Error extracting audio from {video_path}. Error: {e}")
            return gr.update(value=None)
