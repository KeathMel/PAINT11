"""
Windows 11 Paint - Linux Clone
A pixel-perfect 1:1 recreation of Microsoft Paint for Windows 11
Built with pygame for maximum cross-distro compatibility

This is just the entry point now — the actual implementation lives in
paint11_app/ (theme.py, icons.py, model.py, widgets.py, native_dialogs.py,
app.py), split up so a fix to one part doesn't mean touching a 2500-line
file to find it.
"""
import sys
import os
import pygame

pygame.init()
pygame.font.init()

from paint11_app import PaintApp

if __name__ == "__main__":
    open_path = None
    if len(sys.argv) > 1 and os.path.exists(sys.argv[1]):
        open_path = sys.argv[1]
    app = PaintApp(open_path=open_path)
    app.run()
