"""
Native file-open/save dialogs, spawned as a background subprocess.

Why: zenity/kdialog/tkinter can all take a noticeable moment to start up,
especially on a low-RAM machine. The original code called them with
subprocess.run(...) / tkinter's blocking mainloop, which froze the whole
pygame window (no repaint, no event pumping) until the dialog process was
done — the window manager reads that as "not responding". Spawning the
dialog with Popen and polling it from the main loop (see
PaintApp._poll_pending_file_op) keeps the app responsive the entire time.
"""
import os
import shutil
import subprocess
import sys


def _tkinter_open_cmd():
    script = (
        "import tkinter as tk\n"
        "from tkinter import filedialog\n"
        "root = tk.Tk(); root.withdraw()\n"
        "p = filedialog.askopenfilename(\n"
        "    title='Open image',\n"
        "    filetypes=[('Images', '*.png *.jpg *.jpeg *.bmp *.gif *.webp *.tga *.tif *.tiff'),\n"
        "               ('All files', '*.*')])\n"
        "print(p)\n"
    )
    return [sys.executable, "-c", script]


def _tkinter_save_cmd(default_path):
    script = (
        "import tkinter as tk\n"
        "from tkinter import filedialog\n"
        "import os\n"
        f"default = {default_path!r}\n"
        "root = tk.Tk(); root.withdraw()\n"
        "p = filedialog.asksaveasfilename(\n"
        "    title='Save image', defaultextension='.png',\n"
        "    initialfile=os.path.basename(default),\n"
        "    filetypes=[('PNG', '*.png'), ('JPEG', '*.jpg'),\n"
        "               ('Bitmap', '*.bmp'), ('All files', '*.*')])\n"
        "print(p)\n"
    )
    return [sys.executable, "-c", script]


def spawn_open_dialog():
    """Start a file-open dialog in the background. Never blocks — returns
    a subprocess.Popen right away. Poll it with proc.poll()."""
    if shutil.which("zenity"):
        cmd = ["zenity", "--file-selection", "--title=Open image",
               "--file-filter=Images | *.png *.jpg *.jpeg *.bmp *.gif "
               "*.webp *.tga *.tif *.tiff"]
    elif shutil.which("kdialog"):
        cmd = ["kdialog", "--getopenfilename", os.path.expanduser("~"),
               "Images (*.png *.jpg *.jpeg *.bmp *.gif *.webp *.tga *.tif *.tiff)"]
    else:
        cmd = _tkinter_open_cmd()
    return subprocess.Popen(cmd, stdout=subprocess.PIPE,
                             stderr=subprocess.DEVNULL, text=True)


def spawn_save_dialog(default_path):
    """Start a file-save dialog in the background. Never blocks."""
    if shutil.which("zenity"):
        cmd = ["zenity", "--file-selection", "--save", "--confirm-overwrite",
               "--title=Save image", f"--filename={default_path}"]
    elif shutil.which("kdialog"):
        cmd = ["kdialog", "--getsavefilename", default_path,
               "Images (*.png *.jpg *.jpeg *.bmp *.tga)"]
    else:
        cmd = _tkinter_save_cmd(default_path)
    return subprocess.Popen(cmd, stdout=subprocess.PIPE,
                             stderr=subprocess.DEVNULL, text=True)
