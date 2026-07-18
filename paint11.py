"""
Windows 11 Paint - Linux Clone
A pixel-perfect 1:1 recreation of Microsoft Paint for Windows 11
Built with pygame for maximum cross-distro compatibility
"""

import pygame
import pygame.gfxdraw
import sys
import os
import math
import copy
from pathlib import Path

pygame.init()
pygame.font.init()

# ── Windows 11 Fluent Design Color System ─────────────────────────────────────
LIGHT = {
    "bg":          (243, 243, 243),   # Window background
    "toolbar_bg":  (249, 249, 249),   # Toolbar background
    "canvas_bg":   (128, 128, 128),   # Canvas area background (gray surround)
    "titlebar":    (243, 243, 243),   # Title bar
    "border":      (200, 200, 200),   # Borders
    "text":        (0,   0,   0),     # Primary text
    "text_sec":    (97,  97,  97),    # Secondary text
    "accent":      (0,  103, 192),    # Windows 11 blue accent
    "accent_hover":(0,  84,  166),    # Darker accent hover
    "btn_hover":   (219, 219, 219),   # Button hover
    "btn_press":   (200, 200, 200),   # Button pressed
    "btn_active":  (204, 228, 247),   # Active/selected button
    "separator":   (225, 225, 225),   # Toolbar separator
    "white":       (255, 255, 255),   # Pure white
    "canvas_white":(255, 255, 255),   # Canvas itself
    "shadow":      (180, 180, 180),   # Canvas shadow
    "dropdown_bg": (255, 255, 255),   # Dropdown background
    "dropdown_brd":(200, 200, 200),   # Dropdown border
    "statusbar":   (243, 243, 243),   # Status bar
    "statusbar_brd":(210,210,210),    # Status bar top border
    "color_border":(180, 180, 180),   # Color swatch border
    "tooltip_bg":  (50,  50,  50),    # Tooltip background
    "tooltip_text":(255,255,255),     # Tooltip text
}

# ── Dark mode palette (Windows 11 dark) ───────────────────────────────────────
DARK = {
    "bg":          (32,  32,  32),
    "toolbar_bg":  (43,  43,  43),
    "canvas_bg":   (24,  24,  24),    # gray surround around canvas
    "titlebar":    (32,  32,  32),
    "border":      (60,  60,  60),
    "text":        (255, 255, 255),
    "text_sec":    (170, 170, 170),
    "accent":      (96,  205, 255),   # bright blue accent for dark bg
    "accent_hover":(120, 215, 255),
    "btn_hover":   (60,  60,  60),
    "btn_press":   (80,  80,  80),
    "btn_active":  (0,   72,  109),
    "separator":   (55,  55,  55),
    "white":       (50,  50,  50),    # "card" surface in dark mode
    "canvas_white":(255, 255, 255),   # the paper is still white
    "shadow":      (10,  10,  10),
    "dropdown_bg": (50,  50,  50),
    "dropdown_brd":(70,  70,  70),
    "statusbar":   (32,  32,  32),
    "statusbar_brd":(55, 55,  55),
    "color_border":(90,  90,  90),
    "tooltip_bg":  (230, 230, 230),
    "tooltip_text":(20,  20,  20),
}
THEMES = {"light": LIGHT, "dark": DARK}

# ── Font sizes ─────────────────────────────────────────────────────────────────
def load_fonts():
    fonts = {}
    # Try Segoe UI (Windows font if installed), fall back to system fonts
    for name in ("Segoe UI", "Ubuntu", "DejaVu Sans", "Liberation Sans", "Arial"):
        try:
            fonts["ui_sm"]   = pygame.font.SysFont(name, 11)
            fonts["ui"]      = pygame.font.SysFont(name, 13)
            fonts["ui_med"]  = pygame.font.SysFont(name, 13, bold=True)
            fonts["ui_lg"]   = pygame.font.SysFont(name, 15)
            fonts["title"]   = pygame.font.SysFont(name, 12)
            fonts["tooltip"] = pygame.font.SysFont(name, 11)
            break
        except:
            continue
    if "ui" not in fonts:
        fonts["ui_sm"]   = pygame.font.Font(None, 16)
        fonts["ui"]      = pygame.font.Font(None, 18)
        fonts["ui_med"]  = pygame.font.Font(None, 18)
        fonts["ui_lg"]   = pygame.font.Font(None, 20)
        fonts["title"]   = pygame.font.Font(None, 16)
        fonts["tooltip"] = pygame.font.Font(None, 16)
    return fonts

# ── Drawing helpers ────────────────────────────────────────────────────────────
def draw_rounded_rect(surf, color, rect, radius=6, border=0, border_color=None):
    """Draw a rounded rectangle."""
    x, y, w, h = rect
    if w <= 0 or h <= 0:
        return
    radius = min(radius, w // 2, h // 2)
    r = pygame.Rect(rect)
    pygame.draw.rect(surf, color, r, border_radius=radius)
    if border and border_color:
        pygame.draw.rect(surf, border_color, r, border, border_radius=radius)

def draw_text_centered(surf, text, font, color, rect):
    """Draw text centered in a rect."""
    s = font.render(text, True, color)
    x = rect[0] + (rect[2] - s.get_width()) // 2
    y = rect[1] + (rect[3] - s.get_height()) // 2
    surf.blit(s, (x, y))

def draw_text(surf, text, font, color, x, y):
    s = font.render(text, True, color)
    surf.blit(s, (x, y))

def draw_chevron_down(surf, color, cx, cy, size=4):
    pts = [(cx - size, cy - size//2), (cx, cy + size//2), (cx + size, cy - size//2)]
    pygame.draw.lines(surf, color, False, pts, 2)

def draw_icon_pencil(surf, color, x, y, sz=16):
    # Pencil icon
    pts = [(x+sz-3, y+1), (x+sz-1, y+3), (x+3, y+sz-3), (x+1, y+sz-1),
           (x+1, y+sz-1), (x+3, y+sz-3)]
    pygame.draw.line(surf, color, (x+sz-3, y+1), (x+sz-1, y+3), 2)
    pygame.draw.line(surf, color, (x+sz-3, y+1), (x+2, y+sz-2), 2)
    pygame.draw.line(surf, color, (x+sz-1, y+3), (x+4, y+sz-1), 2)
    pygame.draw.line(surf, color, (x+1, y+sz-2), (x+4, y+sz-1), 2)

def draw_icon_eraser(surf, color, x, y, sz=16):
    r = pygame.Rect(x+1, y+sz//2, sz-2, sz//2-1)
    pygame.draw.rect(surf, color, r, border_radius=2)
    pygame.draw.rect(surf, color, r, 1, border_radius=2)
    pygame.draw.line(surf, color, (x+1, y+sz//2), (x+sz//3, y+2), 2)
    pygame.draw.line(surf, color, (x+sz//3, y+2), (x+sz-2, y+sz//2), 2)

def draw_icon_fill(surf, color, x, y, sz=16):
    # Paint bucket
    pts = [(x+4,y+sz-2),(x+2,y+sz-4),(x+2,y+sz//2),(x+sz//2,y+2),(x+sz-2,y+sz//2),(x+sz-2,y+sz-4),(x+sz-4,y+sz-2)]
    if len(pts) > 2:
        pygame.draw.polygon(surf, color, pts[:5], 0)
    pygame.draw.circle(surf, color, (x+sz-3, y+sz-3), 3)

def draw_icon_eyedropper(surf, color, x, y, sz=16):
    pygame.draw.circle(surf, color, (x+sz-4, y+3), 3)
    pygame.draw.line(surf, color, (x+sz-4, y+6), (x+3, y+sz-3), 2)
    pygame.draw.circle(surf, color, (x+3, y+sz-3), 2)

def draw_icon_text(surf, color, x, y, sz=16):
    font = pygame.font.SysFont("DejaVu Sans", sz-2, bold=True)
    s = font.render("A", True, color)
    surf.blit(s, (x + (sz - s.get_width())//2, y + (sz - s.get_height())//2))

def draw_icon_select_rect(surf, color, x, y, sz=16):
    r = pygame.Rect(x+2, y+2, sz-4, sz-4)
    pygame.draw.rect(surf, color, r, 1, border_radius=1)
    # Dashed effect — just draw corners
    pygame.draw.lines(surf, color, False, [(x+2,y+2),(x+8,y+2)], 2)
    pygame.draw.lines(surf, color, False, [(x+2,y+2),(x+2,y+8)], 2)

def draw_icon_select_free(surf, color, x, y, sz=16):
    pts = [(x+4,y+2),(x+sz-2,y+4),(x+sz-3,y+sz-3),(x+2,y+sz-2),(x+4,y+2)]
    pygame.draw.lines(surf, color, False, pts, 2)

def draw_icon_magnify(surf, color, x, y, sz=16):
    pygame.draw.circle(surf, color, (x+6, y+6), 5, 2)
    pygame.draw.line(surf, color, (x+10, y+10), (x+sz-1, y+sz-1), 2)

def draw_icon_resize(surf, color, x, y, sz=16):
    # Resize arrows
    pygame.draw.line(surf, color, (x+1, y+1), (x+sz-2, y+sz-2), 2)
    pygame.draw.line(surf, color, (x+1, y+1), (x+5, y+1), 2)
    pygame.draw.line(surf, color, (x+1, y+1), (x+1, y+5), 2)
    pygame.draw.line(surf, color, (x+sz-2, y+sz-2), (x+sz-2, y+sz-6), 2)
    pygame.draw.line(surf, color, (x+sz-2, y+sz-2), (x+sz-6, y+sz-2), 2)

def draw_icon_crop(surf, color, x, y, sz=16):
    pygame.draw.line(surf, color, (x+3, y+1), (x+3, y+sz-4), 2)
    pygame.draw.line(surf, color, (x+3, y+sz-4), (x+sz-1, y+sz-4), 2)
    pygame.draw.line(surf, color, (x+1, y+3), (x+sz-4, y+3), 2)
    pygame.draw.line(surf, color, (x+sz-4, y+3), (x+sz-4, y+sz-1), 2)

def draw_icon_rotate(surf, color, x, y, sz=16):
    # Arc + arrow
    pygame.draw.arc(surf, color, (x+2, y+2, sz-4, sz-4), 0.3, math.pi*1.7, 2)
    pygame.draw.line(surf, color, (x+sz-3, y+4), (x+sz-3, y+sz//2), 2)
    pygame.draw.line(surf, color, (x+sz-3, y+4), (x+sz//2, y+4), 2)

def draw_icon_flip_h(surf, color, x, y, sz=16):
    cx = x + sz//2
    pygame.draw.line(surf, color, (cx, y+1), (cx, y+sz-2), 2)
    pts1 = [(cx-1, y+sz//2), (cx-5, y+3), (cx-5, y+sz-3)]
    pts2 = [(cx+1, y+sz//2), (cx+5, y+3), (cx+5, y+sz-3)]
    pygame.draw.polygon(surf, color, pts1)
    pygame.draw.polygon(surf, color, pts2)

def draw_icon_line(surf, color, x, y, sz=16):
    pygame.draw.line(surf, color, (x+2, y+sz-3), (x+sz-3, y+2), 2)

def draw_icon_rect_shape(surf, color, x, y, sz=16):
    pygame.draw.rect(surf, color, (x+2, y+3, sz-4, sz-6), 2)

def draw_icon_ellipse_shape(surf, color, x, y, sz=16):
    pygame.draw.ellipse(surf, color, (x+2, y+3, sz-4, sz-6), 2)

def draw_icon_triangle(surf, color, x, y, sz=16):
    pts = [(x+sz//2, y+2), (x+2, y+sz-2), (x+sz-2, y+sz-2)]
    pygame.draw.polygon(surf, color, pts, 2)

def draw_icon_brush(surf, color, x, y, sz=16):
    pygame.draw.line(surf, color, (x+2, y+2), (x+sz-4, y+sz-4), 3)
    pygame.draw.circle(surf, color, (x+sz-3, y+sz-3), 3)

def draw_icon_layers(surf, color, x, y, sz=16):
    for i, offset in enumerate([4, 2, 0]):
        r = pygame.Rect(x+2+offset//2, y+4+i*4-offset, sz-4-offset, 4)
        pygame.draw.rect(surf, color, r, border_radius=1)

def draw_icon_undo(surf, color, x, y, sz=16):
    pygame.draw.arc(surf, color, (x+2, y+2, sz-4, sz-4), math.pi*0.5, math.pi*1.5, 2)
    pts = [(x+2, y+sz//2-1), (x+6, y+3), (x+2, y+4)]
    pygame.draw.polygon(surf, color, pts)

def draw_icon_redo(surf, color, x, y, sz=16):
    pygame.draw.arc(surf, color, (x+2, y+2, sz-4, sz-4), -math.pi*0.5, math.pi*0.5, 2)
    pts = [(x+sz-3, y+sz//2-1), (x+sz-7, y+3), (x+sz-3, y+4)]
    pygame.draw.polygon(surf, color, pts)

def draw_icon_new(surf, color, x, y, sz=16):
    pygame.draw.rect(surf, color, (x+3, y+1, sz-6, sz-2), 1, border_radius=1)
    pygame.draw.line(surf, color, (x+sz//2, y+4), (x+sz//2, y+sz-4), 2)
    pygame.draw.line(surf, color, (x+4, y+sz//2), (x+sz-4, y+sz//2), 2)

def draw_icon_open(surf, color, x, y, sz=16):
    pygame.draw.rect(surf, color, (x+1, y+4, sz-2, sz-5), 1, border_radius=1)
    pygame.draw.rect(surf, color, (x+1, y+4, sz//2-1, 4), 1, border_radius=1)

def draw_icon_save(surf, color, x, y, sz=16):
    pygame.draw.rect(surf, color, (x+1, y+1, sz-2, sz-2), 1, border_radius=1)
    pygame.draw.rect(surf, color, (x+4, y+1, sz-8, 5), 0)
    pygame.draw.rect(surf, color, (x+3, y+9, sz-6, sz-10), 1, border_radius=1)

def draw_icon_ruler(surf, color, x, y, sz=16):
    pygame.draw.rect(surf, color, (x+1, y+sz//2-3, sz-2, 6), 1, border_radius=1)
    for i in range(4):
        pygame.draw.line(surf, color, (x+4+i*3, y+sz//2-3), (x+4+i*3, y+sz//2), 1)

# ══════════════════════════════════════════════════════════════════════════════
# Layer — one transparent sheet in the stack
# ══════════════════════════════════════════════════════════════════════════════
class Layer:
    _counter = 0
    def __init__(self, width, height, name=None, fill=None):
        Layer._counter += 1
        self.name = name or f"Layer {Layer._counter}"
        self.visible = True
        self.surface = pygame.Surface((width, height), pygame.SRCALPHA)
        if fill is not None:
            self.surface.fill(fill)
        else:
            self.surface.fill((0, 0, 0, 0))  # fully transparent


# ══════════════════════════════════════════════════════════════════════════════
# Canvas — holds a stack of layers. self.surface always points at the ACTIVE
# layer's surface, so all existing drawing code keeps working unchanged.
# ══════════════════════════════════════════════════════════════════════════════
class Canvas:
    def __init__(self, width=900, height=600):
        self.width = width
        self.height = height
        self.bg_color = (255, 255, 255)        # canvas background colour
        self.has_background = True             # False = transparent canvas
        # First layer is the "background" layer. It's transparent like any
        # other layer; the opaque white you see comes from has_background.
        base = Layer(width, height, name="Background")
        self.layers = [base]
        self.active_idx = 0
        self.max_history = 50
        self.history = [self._snapshot()]
        self.history_idx = 0

    # -- active layer convenience -------------------------------------------
    @property
    def surface(self):
        return self.layers[self.active_idx].surface

    @surface.setter
    def surface(self, surf):
        # Used by load_image / transforms that replace the whole picture.
        self.layers[self.active_idx].surface = surf

    @property
    def active_layer(self):
        return self.layers[self.active_idx]

    # -- compositing --------------------------------------------------------
    def composite(self):
        """Flatten all visible layers (bottom to top) into one surface.
        If has_background is False the result keeps full transparency."""
        out = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        if self.has_background:
            out.fill((*self.bg_color, 255))
        else:
            out.fill((0, 0, 0, 0))
        for layer in self.layers:
            if layer.visible:
                out.blit(layer.surface, (0, 0))
        return out

    def toggle_background(self):
        self.has_background = not self.has_background

    # -- layer management ---------------------------------------------------
    def add_layer(self):
        lyr = Layer(self.width, self.height)
        self.layers.insert(self.active_idx + 1, lyr)
        self.active_idx += 1
        self.push_history()

    def delete_layer(self, idx=None):
        if idx is None:
            idx = self.active_idx
        if len(self.layers) <= 1:
            return  # never delete the last layer
        self.layers.pop(idx)
        self.active_idx = min(self.active_idx, len(self.layers) - 1)
        self.push_history()

    def duplicate_layer(self, idx=None):
        if idx is None:
            idx = self.active_idx
        src = self.layers[idx]
        dup = Layer(self.width, self.height, name=src.name + " copy")
        dup.surface.blit(src.surface, (0, 0))
        self.layers.insert(idx + 1, dup)
        self.active_idx = idx + 1
        self.push_history()

    def toggle_visible(self, idx):
        self.layers[idx].visible = not self.layers[idx].visible

    def select_layer(self, idx):
        if 0 <= idx < len(self.layers):
            self.active_idx = idx

    def move_layer(self, idx, direction):
        """direction = +1 up (towards top), -1 down."""
        j = idx + direction
        if 0 <= j < len(self.layers):
            self.layers[idx], self.layers[j] = self.layers[j], self.layers[idx]
            if self.active_idx == idx:
                self.active_idx = j
            elif self.active_idx == j:
                self.active_idx = idx
            self.push_history()

    def merge_down(self, idx=None):
        if idx is None:
            idx = self.active_idx
        if idx == 0:
            return  # nothing below
        below = self.layers[idx - 1]
        below.surface.blit(self.layers[idx].surface, (0, 0))
        self.layers.pop(idx)
        self.active_idx = idx - 1
        self.push_history()

    # -- history (snapshots the whole stack) --------------------------------
    def _snapshot(self):
        return {
            "layers": [(l.name, l.visible, l.surface.copy()) for l in self.layers],
            "active": self.active_idx,
            "bg": self.bg_color,
            "has_bg": self.has_background,
        }

    def _restore(self, snap):
        self.layers = []
        for name, visible, surf in snap["layers"]:
            l = Layer(self.width, self.height, name=name)
            l.visible = visible
            l.surface = surf.copy()
            self.layers.append(l)
        self.active_idx = min(snap["active"], len(self.layers) - 1)
        self.bg_color = snap["bg"]
        self.has_background = snap.get("has_bg", True)

    def push_history(self):
        self.history = self.history[:self.history_idx + 1]
        self.history.append(self._snapshot())
        if len(self.history) > self.max_history:
            self.history.pop(0)
        self.history_idx = len(self.history) - 1

    def undo(self):
        if self.history_idx > 0:
            self.history_idx -= 1
            self._restore(self.history[self.history_idx])

    def redo(self):
        if self.history_idx < len(self.history) - 1:
            self.history_idx += 1
            self._restore(self.history[self.history_idx])

    def can_undo(self):
        return self.history_idx > 0

    def can_redo(self):
        return self.history_idx < len(self.history) - 1

    def resize(self, new_w, new_h):
        for l in self.layers:
            ns = pygame.Surface((new_w, new_h), pygame.SRCALPHA)
            ns.fill((0, 0, 0, 0))
            ns.blit(l.surface, (0, 0))
            l.surface = ns
        self.width = new_w
        self.height = new_h
        self.push_history()

    def clear(self):
        self.active_layer.surface.fill((0, 0, 0, 0))
        self.push_history()


# ══════════════════════════════════════════════════════════════════════════════
# Tooltip manager
# ══════════════════════════════════════════════════════════════════════════════
class Tooltip:
    def __init__(self):
        self.text = ""
        self.target_rect = None
        self.visible = False
        self.timer = 0
        self.DELAY = 600  # ms

    def set(self, text, rect):
        if text != self.text or rect != self.target_rect:
            self.text = text
            self.target_rect = rect
            self.timer = pygame.time.get_ticks()
            self.visible = False

    def clear(self):
        self.text = ""
        self.target_rect = None
        self.visible = False

    def update(self):
        if self.text and not self.visible:
            if pygame.time.get_ticks() - self.timer > self.DELAY:
                self.visible = True

    def draw(self, surf, fonts, colors):
        if not self.visible or not self.text:
            return
        pad = 6
        s = fonts["tooltip"].render(self.text, True, colors["tooltip_text"])
        w = s.get_width() + pad*2
        h = s.get_height() + pad*2
        # Position below target rect
        if self.target_rect:
            x = self.target_rect[0]
            y = self.target_rect[1] + self.target_rect[3] + 4
        else:
            x, y = pygame.mouse.get_pos()
        x = min(x, surf.get_width() - w - 4)
        y = min(y, surf.get_height() - h - 4)
        draw_rounded_rect(surf, colors["tooltip_bg"], (x, y, w, h), 4)
        surf.blit(s, (x+pad, y+pad))


# ══════════════════════════════════════════════════════════════════════════════
# Resize Dialog
# ══════════════════════════════════════════════════════════════════════════════
class ResizeDialog:
    def __init__(self, screen_w, screen_h, canvas_w, canvas_h, fonts, colors):
        self.fonts = fonts
        self.colors = colors
        self.w = 360
        self.h = 280
        self.x = (screen_w - self.w) // 2
        self.y = (screen_h - self.h) // 2
        self.canvas_w = canvas_w
        self.canvas_h = canvas_h
        self.width_str = str(canvas_w)
        self.height_str = str(canvas_h)
        self.focused = "width"
        self.maintain_ratio = True
        self.result = None  # None = open, "ok" = confirmed, "cancel" = cancelled
        self.ratio = canvas_w / max(canvas_h, 1)
        # Input field rects (relative to dialog)
        self.width_rect  = (self.x + 150, self.y + 100, 100, 28)
        self.height_rect = (self.x + 150, self.y + 140, 100, 28)
        self.ok_rect     = (self.x + self.w - 180, self.y + self.h - 50, 80, 32)
        self.cancel_rect = (self.x + self.w -  90, self.y + self.h - 50, 80, 32)
        self.ratio_rect  = (self.x + 20, self.y + 185, 16, 16)

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                self.result = "ok"
            elif event.key == pygame.K_ESCAPE:
                self.result = "cancel"
            elif event.key == pygame.K_TAB:
                self.focused = "height" if self.focused == "width" else "width"
            elif event.key == pygame.K_BACKSPACE:
                if self.focused == "width":
                    self.width_str = self.width_str[:-1]
                else:
                    self.height_str = self.height_str[:-1]
            elif event.unicode.isdigit():
                if self.focused == "width":
                    self.width_str += event.unicode
                    if self.maintain_ratio and self.width_str:
                        try:
                            nw = int(self.width_str)
                            self.height_str = str(max(1, int(nw / self.ratio)))
                        except:
                            pass
                else:
                    self.height_str += event.unicode
                    if self.maintain_ratio and self.height_str:
                        try:
                            nh = int(self.height_str)
                            self.width_str = str(max(1, int(nh * self.ratio)))
                        except:
                            pass

        elif event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = event.pos
            if pygame.Rect(self.width_rect).collidepoint(mx, my):
                self.focused = "width"
            elif pygame.Rect(self.height_rect).collidepoint(mx, my):
                self.focused = "height"
            elif pygame.Rect(self.ok_rect).collidepoint(mx, my):
                self.result = "ok"
            elif pygame.Rect(self.cancel_rect).collidepoint(mx, my):
                self.result = "cancel"
            elif pygame.Rect(self.ratio_rect).collidepoint(mx, my):
                self.maintain_ratio = not self.maintain_ratio
            elif not pygame.Rect(self.x, self.y, self.w, self.h).collidepoint(mx, my):
                self.result = "cancel"

    def get_values(self):
        try:
            w = max(1, min(10000, int(self.width_str)))
            h = max(1, min(10000, int(self.height_str)))
            return w, h
        except:
            return self.canvas_w, self.canvas_h

    def draw(self, surf):
        c = self.colors
        f = self.fonts
        # Shadow
        shadow = pygame.Surface((self.w+8, self.h+8), pygame.SRCALPHA)
        shadow.fill((0, 0, 0, 40))
        surf.blit(shadow, (self.x-2, self.y+4))
        # Dialog bg
        draw_rounded_rect(surf, c["white"], (self.x, self.y, self.w, self.h), 8, 1, c["border"])
        # Title bar
        draw_rounded_rect(surf, c["toolbar_bg"], (self.x, self.y, self.w, 40), 8)
        pygame.draw.rect(surf, c["toolbar_bg"], (self.x, self.y+20, self.w, 20))
        pygame.draw.line(surf, c["border"], (self.x, self.y+40), (self.x+self.w, self.y+40), 1)
        draw_text(surf, "Resize canvas", f["ui_med"], c["text"], self.x+16, self.y+12)
        # Fields
        draw_text(surf, "Width:", f["ui"], c["text"], self.x+20, self.y+107)
        draw_text(surf, "Height:", f["ui"], c["text"], self.x+20, self.y+147)
        # Input boxes
        for label, rect, val, focused_key in [
            ("width", self.width_rect, self.width_str, "width"),
            ("height", self.height_rect, self.height_str, "height"),
        ]:
            is_focused = self.focused == focused_key
            bc = c["accent"] if is_focused else c["border"]
            bw = 2 if is_focused else 1
            draw_rounded_rect(surf, c["white"], rect, 4, bw, bc)
            txt = val + ("|" if is_focused and (pygame.time.get_ticks() // 500) % 2 == 0 else "")
            s = f["ui"].render(txt, True, c["text"])
            surf.blit(s, (rect[0]+6, rect[1]+(rect[3]-s.get_height())//2))
        # Pixels label
        draw_text(surf, "pixels", f["ui"], c["text_sec"], self.x+258, self.y+107)
        draw_text(surf, "pixels", f["ui"], c["text_sec"], self.x+258, self.y+147)
        # Maintain ratio checkbox
        checkbox_rect = self.ratio_rect
        draw_rounded_rect(surf, c["white"], checkbox_rect, 3, 1, c["border"])
        if self.maintain_ratio:
            pygame.draw.line(surf, c["accent"], 
                (checkbox_rect[0]+2, checkbox_rect[1]+8),
                (checkbox_rect[0]+6, checkbox_rect[1]+12), 2)
            pygame.draw.line(surf, c["accent"],
                (checkbox_rect[0]+6, checkbox_rect[1]+12),
                (checkbox_rect[0]+13, checkbox_rect[1]+3), 2)
        draw_text(surf, "Maintain aspect ratio", f["ui"], c["text"], self.x+42, self.y+187)
        # Buttons
        mx, my = pygame.mouse.get_pos()
        for label, rect, is_primary in [("OK", self.ok_rect, True), ("Cancel", self.cancel_rect, False)]:
            hov = pygame.Rect(rect).collidepoint(mx, my)
            if is_primary:
                bg = c["accent_hover"] if hov else c["accent"]
                draw_rounded_rect(surf, bg, rect, 4)
                draw_text_centered(surf, label, f["ui_med"], c["white"], rect)
            else:
                bg = c["btn_hover"] if hov else c["white"]
                draw_rounded_rect(surf, bg, rect, 4, 1, c["border"])
                draw_text_centered(surf, label, f["ui"], c["text"], rect)


# ══════════════════════════════════════════════════════════════════════════════
# Color Picker Dialog
# ══════════════════════════════════════════════════════════════════════════════
class ColorPickerDialog:
    def __init__(self, screen_w, screen_h, current_color, fonts, colors):
        self.fonts = fonts
        self.colors = colors
        self.w = 420
        self.h = 380
        self.x = (screen_w - self.w) // 2
        self.y = (screen_h - self.h) // 2
        self.current_color = list(current_color[:3])
        self.result = None
        self.dragging_spectrum = False
        self.dragging_hue = False
        self.spec_rect = (self.x + 20, self.y + 55, 200, 200)
        self.hue_rect  = (self.x + 235, self.y + 55, 20, 200)
        self.ok_rect     = (self.x + self.w - 180, self.y + self.h - 50, 80, 32)
        self.cancel_rect = (self.x + self.w -  90, self.y + self.h - 50, 80, 32)
        # RGB inputs
        self.rgb_strs = [str(c) for c in self.current_color]
        self.rgb_focused = -1
        self.rgb_rects = [
            (self.x + 275, self.y + 80  + i*36, 80, 26) for i in range(3)
        ]
        # Pre-render spectrum and hue
        self._h, self._s, self._v = self._rgb_to_hsv(*self.current_color)
        self._spectrum_surf = None
        self._hue_surf = None
        self._build_hue_surf()
        self._build_spectrum_surf()

    def _rgb_to_hsv(self, r, g, b):
        r, g, b = r/255.0, g/255.0, b/255.0
        mx = max(r,g,b); mn = min(r,g,b); df = mx-mn
        if mx == mn: h = 0
        elif mx == r: h = (60*((g-b)/df) + 360) % 360
        elif mx == g: h = (60*((b-r)/df) + 120) % 360
        else:         h = (60*((r-g)/df) + 240) % 360
        s = 0 if mx == 0 else df/mx
        v = mx
        return h, s, v

    def _hsv_to_rgb(self, h, s, v):
        if s == 0: r=g=b=v
        else:
            i = int(h/60) % 6
            f = h/60 - int(h/60)
            p,q,t = v*(1-s), v*(1-s*f), v*(1-s*(1-f))
            r,g,b = [(v,t,p),(q,v,p),(p,v,t),(p,q,v),(t,p,v),(v,p,q)][i]
        return int(r*255), int(g*255), int(b*255)

    def _build_hue_surf(self):
        sw, sh = self.hue_rect[2], self.hue_rect[3]
        self._hue_surf = pygame.Surface((sw, sh))
        for y in range(sh):
            h = (y / sh) * 360
            r,g,b = self._hsv_to_rgb(h, 1, 1)
            pygame.draw.line(self._hue_surf, (r,g,b), (0,y), (sw-1,y))

    def _build_spectrum_surf(self):
        sw, sh = self.spec_rect[2], self.spec_rect[3]
        self._spectrum_surf = pygame.Surface((sw, sh))
        for x in range(sw):
            s = x / sw
            for y in range(sh):
                v = 1.0 - y / sh
                r,g,b = self._hsv_to_rgb(self._h, s, v)
                self._spectrum_surf.set_at((x, y), (r,g,b))

    def _update_color_from_hsv(self):
        self.current_color = list(self._hsv_to_rgb(self._h, self._s, self._v))
        self.rgb_strs = [str(c) for c in self.current_color]

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = event.pos
            sx, sy, sw, sh = self.spec_rect
            hx, hy, hw, hh = self.hue_rect
            if pygame.Rect(self.spec_rect).collidepoint(mx, my):
                self.dragging_spectrum = True
                self._s = (mx - sx) / sw
                self._v = 1.0 - (my - sy) / sh
                self._s = max(0, min(1, self._s))
                self._v = max(0, min(1, self._v))
                self._update_color_from_hsv()
            elif pygame.Rect(self.hue_rect).collidepoint(mx, my):
                self.dragging_hue = True
                self._h = ((my - hy) / hh) * 360
                self._h = max(0, min(360, self._h))
                self._build_spectrum_surf()
                self._update_color_from_hsv()
            elif pygame.Rect(self.ok_rect).collidepoint(mx, my):
                self.result = "ok"
            elif pygame.Rect(self.cancel_rect).collidepoint(mx, my):
                self.result = "cancel"
            else:
                for i, r in enumerate(self.rgb_rects):
                    if pygame.Rect(r).collidepoint(mx, my):
                        self.rgb_focused = i
                        break
                else:
                    if not pygame.Rect(self.x, self.y, self.w, self.h).collidepoint(mx, my):
                        self.result = "cancel"
                    else:
                        self.rgb_focused = -1

        elif event.type == pygame.MOUSEBUTTONUP:
            self.dragging_spectrum = False
            self.dragging_hue = False

        elif event.type == pygame.MOUSEMOTION:
            mx, my = event.pos
            sx, sy, sw, sh = self.spec_rect
            hx, hy, hw, hh = self.hue_rect
            if self.dragging_spectrum:
                self._s = max(0, min(1, (mx - sx) / sw))
                self._v = max(0, min(1, 1.0 - (my - sy) / sh))
                self._update_color_from_hsv()
            elif self.dragging_hue:
                self._h = max(0, min(360, ((my - hy) / hh) * 360))
                self._build_spectrum_surf()
                self._update_color_from_hsv()

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.result = "cancel"
            elif event.key == pygame.K_RETURN:
                self.result = "ok"
            elif event.key == pygame.K_TAB:
                self.rgb_focused = (self.rgb_focused + 1) % 3
            elif self.rgb_focused >= 0:
                if event.key == pygame.K_BACKSPACE:
                    self.rgb_strs[self.rgb_focused] = self.rgb_strs[self.rgb_focused][:-1]
                elif event.unicode.isdigit():
                    self.rgb_strs[self.rgb_focused] += event.unicode
                    try:
                        val = max(0, min(255, int(self.rgb_strs[self.rgb_focused])))
                        self.current_color[self.rgb_focused] = val
                        self._h, self._s, self._v = self._rgb_to_hsv(*self.current_color)
                        self._build_spectrum_surf()
                    except:
                        pass

    def draw(self, surf):
        c = self.colors
        f = self.fonts
        draw_rounded_rect(surf, c["white"], (self.x, self.y, self.w, self.h), 8, 1, c["border"])
        draw_rounded_rect(surf, c["toolbar_bg"], (self.x, self.y, self.w, 40), 8)
        pygame.draw.rect(surf, c["toolbar_bg"], (self.x, self.y+20, self.w, 20))
        pygame.draw.line(surf, c["border"], (self.x, self.y+40), (self.x+self.w, self.y+40), 1)
        draw_text(surf, "Edit color", f["ui_med"], c["text"], self.x+16, self.y+12)
        # Spectrum
        if self._spectrum_surf:
            surf.blit(self._spectrum_surf, self.spec_rect[:2])
            pygame.draw.rect(surf, c["border"], self.spec_rect, 1)
            # Cursor
            sx, sy, sw, sh = self.spec_rect
            cx = int(sx + self._s * sw)
            cy = int(sy + (1.0 - self._v) * sh)
            pygame.draw.circle(surf, (255,255,255), (cx, cy), 6, 2)
            pygame.draw.circle(surf, (0,0,0), (cx, cy), 7, 1)
        # Hue bar
        if self._hue_surf:
            surf.blit(self._hue_surf, self.hue_rect[:2])
            pygame.draw.rect(surf, c["border"], self.hue_rect, 1)
            hx, hy, hw, hh = self.hue_rect
            hy_cursor = int(hy + (self._h / 360) * hh)
            pygame.draw.rect(surf, (255,255,255), (hx-2, hy_cursor-2, hw+4, 4), 2)
        # Color preview
        preview_rect = (self.x + 270, self.y + 270, 60, 40)
        draw_rounded_rect(surf, tuple(self.current_color), preview_rect, 4, 1, c["border"])
        draw_text(surf, "Preview", f["ui"], c["text_sec"], self.x+270, self.y+316)
        # RGB inputs
        rgb_labels = ["R:", "G:", "B:"]
        for i, (label, rect) in enumerate(zip(rgb_labels, self.rgb_rects)):
            draw_text(surf, label, f["ui"], c["text"], self.x+260, rect[1]+5)
            is_focused = self.rgb_focused == i
            bc = c["accent"] if is_focused else c["border"]
            draw_rounded_rect(surf, c["white"], rect, 4, 2 if is_focused else 1, bc)
            val = self.rgb_strs[i] + ("|" if is_focused and (pygame.time.get_ticks()//500)%2==0 else "")
            s = f["ui"].render(val, True, c["text"])
            surf.blit(s, (rect[0]+6, rect[1]+(rect[3]-s.get_height())//2))
        # Buttons
        mx, my = pygame.mouse.get_pos()
        for label, rect, is_primary in [("OK", self.ok_rect, True), ("Cancel", self.cancel_rect, False)]:
            hov = pygame.Rect(rect).collidepoint(mx, my)
            if is_primary:
                bg = c["accent_hover"] if hov else c["accent"]
                draw_rounded_rect(surf, bg, rect, 4)
                draw_text_centered(surf, label, f["ui_med"], c["white"], rect)
            else:
                bg = c["btn_hover"] if hov else c["white"]
                draw_rounded_rect(surf, bg, rect, 4, 1, c["border"])
                draw_text_centered(surf, label, f["ui"], c["text"], rect)


# ══════════════════════════════════════════════════════════════════════════════
# Main Paint Application
# ══════════════════════════════════════════════════════════════════════════════
class PaintApp:
    TITLE_H    = 40
    TOOLBAR_H  = 64
    STATUSBAR_H = 24

    # W11 default palette
    DEFAULT_PALETTE = [
        (0,0,0),(255,255,255),(128,128,128),(192,192,192),
        (255,0,0),(255,128,0),(255,255,0),(0,255,0),
        (0,255,255),(0,0,255),(128,0,255),(255,0,255),
        (128,0,0),(128,64,0),(128,128,0),(0,128,0),
        (0,128,128),(0,0,128),(64,0,128),(128,0,128),
        (255,128,128),(255,192,128),(255,255,128),(128,255,128),
        (128,255,255),(128,128,255),(192,128,255),(255,128,255),
        (180,80,80),(100,60,20),
    ]

    def __init__(self, open_path=None):
        self.SCREEN_W = 1280
        self.SCREEN_H = 768
        self.screen = pygame.display.set_mode(
            (self.SCREEN_W, self.SCREEN_H),
            pygame.RESIZABLE
        )
        pygame.display.set_caption("Paint")
        self._pending_open = open_path
        self.clock = pygame.time.Clock()
        self.fonts = load_fonts()
        self.theme = "dark"          # dark mode on by default
        self.colors = THEMES[self.theme]
        self.canvas = Canvas(900, 600)
        self.zoom = 1.0
        self.scroll_x = 0
        self.scroll_y = 0
        self.color1 = (0, 0, 0)    # Primary
        self.color2 = (255, 255, 255)  # Secondary
        self.tool = "pencil"
        self.brush_size = 3
        self.shape_fill = False
        self.shape_outline = True
        self.drawing = False
        self.last_pos = None
        self.start_pos = None
        self.preview_surface = None
        self.selection = None      # (x,y,w,h) on canvas
        self.selection_active = False
        self.selection_moving = False
        self.sel_move_start = None
        self.sel_move_offset = (0, 0)
        self.selection_copy = None  # Surface
        self.freeform_points = []
        self.text_box = None        # (x,y) on canvas
        self.text_content = ""
        self.text_font_name = "Arial"
        self.text_font_size = 14
        self.palette = list(self.DEFAULT_PALETTE)
        self.show_grid = False
        self.show_rulers = True
        self.dialog = None
        self.dropdown = None   # ("menu_name", x, y)
        self.tooltip = Tooltip()
        self.title_modified = False
        self.current_file = None
        self.layers_panel_open = False

        self._calc_layout()

        # If a file was passed on the command line, open it now
        if self._pending_open:
            self.load_image(self._pending_open)

    LAYER_PANEL_W = 220

    def _calc_layout(self):
        sw = self.SCREEN_W
        sh = self.SCREEN_H
        self.title_rect    = pygame.Rect(0, 0, sw, self.TITLE_H)
        self.toolbar_rect  = pygame.Rect(0, self.TITLE_H, sw, self.TOOLBAR_H)
        panel_w = self.LAYER_PANEL_W if getattr(self, "layers_panel_open", False) else 0
        self.canvas_area   = pygame.Rect(
            0,
            self.TITLE_H + self.TOOLBAR_H,
            sw - panel_w,
            sh - self.TITLE_H - self.TOOLBAR_H - self.STATUSBAR_H
        )
        self.layer_panel_rect = pygame.Rect(
            sw - panel_w, self.TITLE_H + self.TOOLBAR_H,
            panel_w, sh - self.TITLE_H - self.TOOLBAR_H - self.STATUSBAR_H
        )
        self.statusbar_rect = pygame.Rect(0, sh - self.STATUSBAR_H, sw, self.STATUSBAR_H)
        # Auto-center canvas
        self._fit_canvas()

    def _fit_canvas(self):
        """Center canvas in canvas area."""
        cw = int(self.canvas.width * self.zoom)
        ch = int(self.canvas.height * self.zoom)
        ca = self.canvas_area
        self.scroll_x = max(0, (ca.width - cw) // 2)
        self.scroll_y = max(0, (ca.height - ch) // 2)

    def canvas_to_screen(self, cx, cy):
        ca = self.canvas_area
        return (
            ca.x + self.scroll_x + int(cx * self.zoom),
            ca.y + self.scroll_y + int(cy * self.zoom)
        )

    def screen_to_canvas(self, sx, sy):
        ca = self.canvas_area
        cx = (sx - ca.x - self.scroll_x) / self.zoom
        cy = (sy - ca.y - self.scroll_y) / self.zoom
        return int(cx), int(cy)

    # ── Drawing: tools ──────────────────────────────────────────────────────
    def draw_on_canvas(self, pos, color, force_end=False):
        tool = self.tool
        cx, cy = pos

        if tool == "pencil":
            if self.last_pos:
                pygame.draw.line(self.canvas.surface, color,
                                 self.last_pos, (cx, cy), max(1, self.brush_size))
            else:
                pygame.draw.circle(self.canvas.surface, color, (cx, cy), max(0, self.brush_size//2))
            self.last_pos = (cx, cy)

        elif tool == "brush":
            if self.last_pos:
                pygame.draw.line(self.canvas.surface, color,
                                 self.last_pos, (cx, cy), self.brush_size*2)
            else:
                pygame.draw.circle(self.canvas.surface, color, (cx, cy), self.brush_size)
            self.last_pos = (cx, cy)

        elif tool == "eraser":
            sz = self.brush_size * 4
            r = pygame.Rect(cx - sz//2, cy - sz//2, sz, sz)
            # Erase to transparent so lower layers show through (W11 behaviour)
            self.canvas.surface.fill((0, 0, 0, 0), r)
            self.last_pos = (cx, cy)

        elif tool == "fill":
            self._flood_fill(cx, cy, color)

        elif tool == "eyedropper":
            if 0 <= cx < self.canvas.width and 0 <= cy < self.canvas.height:
                picked = self.canvas.surface.get_at((cx, cy))[:3]
                if self._drawing_with_left:
                    self.color1 = picked
                else:
                    self.color2 = picked
                self.tool = self._prev_tool or "pencil"

    def _flood_fill(self, x, y, fill_color):
        surface = self.canvas.surface
        w, h = self.canvas.width, self.canvas.height
        if not (0 <= x < w and 0 <= y < h):
            return
        # Fill colour is opaque
        fc = (int(fill_color[0]), int(fill_color[1]), int(fill_color[2]), 255)
        # Compare full RGBA so it works on transparent layers too
        target = surface.get_at((x, y))
        target = (target[0], target[1], target[2], target[3])
        if target == fc:
            return
        try:
            pa = pygame.PixelArray(surface)
            fill_c = surface.map_rgb(fc)
            tgt_c  = surface.map_rgb(target)
            if fill_c == tgt_c:
                del pa
                return
            stack = [(x, y)]
            seen_cols = w
            while stack:
                px, py = stack.pop()
                if px < 0 or px >= w or py < 0 or py >= h:
                    continue
                if pa[px, py] != tgt_c:
                    continue
                # scan left/right for speed
                lx = px
                while lx - 1 >= 0 and pa[lx - 1, py] == tgt_c:
                    lx -= 1
                rx = px
                while rx + 1 < w and pa[rx + 1, py] == tgt_c:
                    rx += 1
                for sx in range(lx, rx + 1):
                    pa[sx, py] = fill_c
                    if py - 1 >= 0 and pa[sx, py - 1] == tgt_c:
                        stack.append((sx, py - 1))
                    if py + 1 < h and pa[sx, py + 1] == tgt_c:
                        stack.append((sx, py + 1))
            del pa
        except Exception as e:
            print("flood fill error:", e)

    def _draw_shape_preview(self, surf, start, end, color, tool):
        x1, y1 = start
        x2, y2 = end
        lw = max(1, self.brush_size)
        if tool == "line":
            pygame.draw.line(surf, color, (x1,y1), (x2,y2), lw)
        elif tool == "rect":
            r = pygame.Rect(min(x1,x2), min(y1,y2), abs(x2-x1), abs(y2-y1))
            if self.shape_fill:
                pygame.draw.rect(surf, color, r)
            if self.shape_outline:
                pygame.draw.rect(surf, color, r, lw)
        elif tool == "ellipse":
            r = pygame.Rect(min(x1,x2), min(y1,y2), abs(x2-x1), abs(y2-y1))
            if r.width > 0 and r.height > 0:
                if self.shape_fill:
                    pygame.draw.ellipse(surf, color, r)
                if self.shape_outline:
                    pygame.draw.ellipse(surf, color, r, lw)
        elif tool == "triangle":
            mx = (x1+x2)//2
            pts = [(mx, y1), (x1, y2), (x2, y2)]
            if self.shape_fill:
                pygame.draw.polygon(surf, color, pts)
            if self.shape_outline:
                pygame.draw.polygon(surf, color, pts, lw)
        elif tool == "rounded_rect":
            r = pygame.Rect(min(x1,x2), min(y1,y2), abs(x2-x1), abs(y2-y1))
            if r.width > 4 and r.height > 4:
                if self.shape_fill:
                    pygame.draw.rect(surf, color, r, border_radius=12)
                if self.shape_outline:
                    pygame.draw.rect(surf, color, r, lw, border_radius=12)

    # ── Event handling ───────────────────────────────────────────────────────
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

            # Drag-and-drop a file onto the window to open it
            if event.type == pygame.DROPFILE:
                self.load_image(event.file)
                continue

            if event.type == pygame.VIDEORESIZE:
                self.SCREEN_W, self.SCREEN_H = event.w, event.h
                self._calc_layout()

            # Dialog takes priority
            if self.dialog:
                self.dialog.handle_event(event)
                if self.dialog.result == "ok":
                    if isinstance(self.dialog, ResizeDialog):
                        nw, nh = self.dialog.get_values()
                        self.canvas.resize(nw, nh)
                        self._fit_canvas()
                    elif isinstance(self.dialog, ColorPickerDialog):
                        if self.dialog._editing_primary:
                            self.color1 = tuple(self.dialog.current_color)
                        else:
                            self.color2 = tuple(self.dialog.current_color)
                    self.dialog = None
                elif self.dialog.result == "cancel":
                    self.dialog = None
                continue

            if event.type == pygame.KEYDOWN:
                self._handle_key(event)

            if event.type == pygame.MOUSEBUTTONDOWN:
                self._handle_mouse_down(event)

            if event.type == pygame.MOUSEBUTTONUP:
                self._handle_mouse_up(event)

            if event.type == pygame.MOUSEMOTION:
                self._handle_mouse_move(event)

            if event.type == pygame.MOUSEWHEEL:
                self._handle_wheel(event)

        return True

    def _handle_key(self, event):
        mods = pygame.key.get_mods()
        ctrl = mods & pygame.KMOD_CTRL
        if ctrl:
            if event.key == pygame.K_z:
                if mods & pygame.KMOD_SHIFT:
                    self.canvas.redo()
                else:
                    self.canvas.undo()
            elif event.key == pygame.K_y:
                self.canvas.redo()
            elif event.key == pygame.K_s:
                self._save_file(save_as=(mods & pygame.KMOD_SHIFT) > 0)
            elif event.key == pygame.K_o:
                self._open_file()
            elif event.key == pygame.K_n:
                self._new_file()
            elif event.key == pygame.K_a:
                self.selection = (0, 0, self.canvas.width, self.canvas.height)
                self.selection_active = True
            elif event.key == pygame.K_c:
                if self.selection_active and self.selection:
                    self._copy_selection()
            elif event.key == pygame.K_v:
                self._paste()
            elif event.key == pygame.K_x:
                if self.selection_active and self.selection:
                    self._cut_selection()
            elif event.key == pygame.K_PLUS or event.key == pygame.K_EQUALS:
                self.zoom = min(16.0, self.zoom * 1.25)
            elif event.key == pygame.K_MINUS:
                self.zoom = max(0.1, self.zoom / 1.25)
            elif event.key == pygame.K_0:
                self.zoom = 1.0
                self._fit_canvas()
            elif event.key == pygame.K_l:
                self.toggle_layers_panel()
            elif event.key == pygame.K_d:
                self.toggle_theme()
            elif event.key == pygame.K_n and (mods & pygame.KMOD_SHIFT):
                self.canvas.add_layer()
        else:
            if event.key == pygame.K_ESCAPE:
                self.selection_active = False
                self.selection = None
                self.dropdown = None
            if self.tool == "text" and self.text_box:
                if event.key == pygame.K_BACKSPACE:
                    self.text_content = self.text_content[:-1]
                elif event.key == pygame.K_RETURN:
                    self._commit_text()
                elif event.key == pygame.K_ESCAPE:
                    self.text_box = None
                    self.text_content = ""
                elif event.unicode and event.unicode.isprintable():
                    self.text_content += event.unicode

    def _handle_mouse_down(self, event):
        mx, my = event.pos
        btn = event.button

        # Close dropdown on click outside
        if self.dropdown:
            if not self._in_dropdown(mx, my):
                self.dropdown = None
            else:
                self._handle_dropdown_click(mx, my)
                return

        # Title bar buttons
        if self.title_rect.collidepoint(mx, my):
            self._handle_titlebar_click(mx, my)
            return

        # Toolbar
        if self.toolbar_rect.collidepoint(mx, my):
            self._handle_toolbar_click(mx, my, btn)
            return

        # Layers panel
        if self.layers_panel_open and self.layer_panel_rect.collidepoint(mx, my):
            self._handle_layer_panel_click(mx, my)
            return

        # Canvas area
        if self.canvas_area.collidepoint(mx, my):
            cx, cy = self.screen_to_canvas(mx, my)
            self._drawing_with_left = (btn == 1)
            color = self.color1 if btn == 1 else self.color2

            if self.tool == "select_rect":
                # Check if clicking inside existing selection to move
                if self.selection_active and self.selection:
                    sx,sy,sw,sh = self.selection
                    if sx <= cx <= sx+sw and sy <= cy <= sy+sh:
                        sw2 = min(sw, self.canvas.width - sx)
                        sh2 = min(sh, self.canvas.height - sy)
                        if sw2 > 0 and sh2 > 0:
                            self.selection_moving = True
                            self.sel_move_start = (cx, cy)
                            self._sel_origin = (sx, sy)
                            self.canvas.push_history()
                            # Copy of the pixels being moved
                            self.selection_copy = self.canvas.surface.subsurface(
                                pygame.Rect(sx, sy, sw2, sh2)).copy()
                            # Clean base = active layer with the selection
                            # area punched out ONCE. Every move redraws from
                            # this so we don't trail erased rectangles.
                            self._move_base = self.canvas.surface.copy()
                            self._move_base.fill((0, 0, 0, 0),
                                                 pygame.Rect(sx, sy, sw2, sh2))
                        return
                self.selection_active = False
                self.selection = None
                self.start_pos = (cx, cy)
                self.drawing = True

            elif self.tool == "select_free":
                self.freeform_points = [(cx, cy)]
                self.drawing = True

            elif self.tool in ("pencil","brush","eraser"):
                self.canvas.push_history()
                self.drawing = True
                self.last_pos = None
                self.draw_on_canvas((cx,cy), color)

            elif self.tool == "fill":
                self.canvas.push_history()
                self.draw_on_canvas((cx,cy), color)

            elif self.tool == "eyedropper":
                self._prev_tool = self.tool
                self.draw_on_canvas((cx,cy), color)

            elif self.tool in ("line","rect","ellipse","triangle","rounded_rect"):
                self.start_pos = (cx, cy)
                self.drawing = True
                self.preview_surface = self.canvas.surface.copy()

            elif self.tool == "text":
                if self.text_box:
                    self._commit_text()
                self.text_box = (cx, cy)
                self.text_content = ""

    def _handle_mouse_up(self, event):
        mx, my = event.pos
        cx, cy = self.screen_to_canvas(mx, my)

        if self.selection_moving:
            self.selection_moving = False
            self.sel_move_start = None
            self.selection_copy = None
            self._move_base = None
            return

        if not self.drawing:
            return

        if self.tool == "select_rect":
            if self.start_pos:
                sx = min(self.start_pos[0], cx)
                sy = min(self.start_pos[1], cy)
                sw = abs(cx - self.start_pos[0])
                sh = abs(cy - self.start_pos[1])
                if sw > 2 and sh > 2:
                    sx = max(0, min(sx, self.canvas.width-1))
                    sy = max(0, min(sy, self.canvas.height-1))
                    sw = min(sw, self.canvas.width - sx)
                    sh = min(sh, self.canvas.height - sy)
                    self.selection = (sx, sy, sw, sh)
                    self.selection_active = True
                    self.selection_copy = None

        elif self.tool == "select_free":
            if len(self.freeform_points) > 2:
                self.selection_active = True
                # Bounding box
                xs = [p[0] for p in self.freeform_points]
                ys = [p[1] for p in self.freeform_points]
                self.selection = (min(xs), min(ys), max(xs)-min(xs), max(ys)-min(ys))

        elif self.tool in ("line","rect","ellipse","triangle","rounded_rect"):
            if self.start_pos and self.preview_surface:
                self.canvas.surface.blit(self.preview_surface, (0,0))
                color = self.color1 if self._drawing_with_left else self.color2
                self._draw_shape_preview(self.canvas.surface, self.start_pos, (cx,cy), color, self.tool)
                self.canvas.push_history()
            self.start_pos = None
            self.preview_surface = None

        elif self.tool in ("pencil","brush","eraser"):
            self.canvas.push_history()

        self.drawing = False
        self.last_pos = None
        self.start_pos = None

    def _handle_mouse_move(self, event):
        mx, my = event.pos
        cx, cy = self.screen_to_canvas(mx, my)

        # Tooltip update based on toolbar hover
        if self.toolbar_rect.collidepoint(mx, my):
            self._update_toolbar_tooltip(mx, my)
        else:
            self.tooltip.clear()

        if self.selection_moving and self.sel_move_start:
            dx = cx - self.sel_move_start[0]
            dy = cy - self.sel_move_start[1]
            sx, sy, sw, sh = self.selection
            # new top-left, original size, clamped to canvas
            ox, oy = self._sel_origin if hasattr(self, "_sel_origin") else (sx, sy)
            new_sx = max(0, min(self.canvas.width - sw, ox + dx))
            new_sy = max(0, min(self.canvas.height - sh, oy + dy))
            if self.selection_copy and getattr(self, "_move_base", None) is not None:
                surface = self.canvas.surface
                # Start from the clean base (hole already punched once)
                surface.blit(self._move_base, (0, 0))
                # Stamp the moved pixels at the new position
                surface.blit(self.selection_copy, (new_sx, new_sy))
            self.selection = (new_sx, new_sy, sw, sh)
            return

        if not self.drawing:
            return

        color = self.color1 if self._drawing_with_left else self.color2

        if self.tool == "select_rect" and self.start_pos:
            pass  # Drawn in render

        elif self.tool == "select_free":
            if (cx, cy) != self.freeform_points[-1]:
                self.freeform_points.append((cx, cy))

        elif self.tool in ("pencil","brush","eraser"):
            self.draw_on_canvas((cx,cy), color)

        elif self.tool in ("line","rect","ellipse","triangle","rounded_rect"):
            pass  # Drawn in render as preview

    def _handle_wheel(self, event):
        mods = pygame.key.get_mods()
        if mods & pygame.KMOD_CTRL:
            if event.y > 0:
                self.zoom = min(16.0, self.zoom * 1.1)
            else:
                self.zoom = max(0.05, self.zoom / 1.1)
        else:
            if mods & pygame.KMOD_SHIFT:
                self.scroll_x -= event.y * 30
            else:
                self.scroll_y -= event.y * 30

    def _handle_titlebar_click(self, mx, my):
        # Menu buttons
        menus = self._get_menu_buttons()
        for name, rect in menus.items():
            if pygame.Rect(rect).collidepoint(mx, my):
                if self.dropdown and self.dropdown[0] == name:
                    self.dropdown = None
                else:
                    self.dropdown = (name, rect[0], rect[1]+rect[3])
                return
        # Quick action buttons (undo, redo, save)
        for name, rect in self._get_quick_actions():
            if pygame.Rect(rect).collidepoint(mx, my):
                if name == "undo":    self.canvas.undo()
                elif name == "redo":  self.canvas.redo()
                elif name == "save":  self._save_file()
                return

    def _handle_toolbar_click(self, mx, my, btn):
        # Action buttons (perform immediately, not selectable "tools")
        ACTIONS = {
            "resize": lambda: setattr(self, 'dialog',
                ResizeDialog(self.SCREEN_W, self.SCREEN_H,
                             self.canvas.width, self.canvas.height,
                             self.fonts, self.colors)),
            "crop":   self._crop_to_selection,
            "rotate": self._rotate_canvas,
            "flip":   self._flip_h,
        }
        # Tool buttons
        for name, rect in self._get_tool_buttons():
            if pygame.Rect(rect).collidepoint(mx, my):
                if name in ACTIONS:
                    ACTIONS[name]()
                    return
                self.tool = name
                if name in ("select_rect","select_free"):
                    pass
                else:
                    self.selection_active = False
                    self.selection = None
                return
        # Brush size buttons
        for size, rect in self._get_size_buttons():
            if pygame.Rect(rect).collidepoint(mx, my):
                self.brush_size = size
                return
        # Color swatches
        for i, rect in enumerate(self._get_palette_rects()):
            if pygame.Rect(rect).collidepoint(mx, my):
                if btn == 1:
                    self.color1 = self.palette[i]
                elif btn == 3:
                    self.color2 = self.palette[i]
                return
        # Color preview (big circles) - open color picker
        c1_rect, c2_rect = self._get_color_circles()
        if pygame.Rect(c1_rect).collidepoint(mx, my):
            self.dialog = ColorPickerDialog(
                self.SCREEN_W, self.SCREEN_H, self.color1, self.fonts, self.colors)
            self.dialog._editing_primary = True
            return
        if pygame.Rect(c2_rect).collidepoint(mx, my):
            self.dialog = ColorPickerDialog(
                self.SCREEN_W, self.SCREEN_H, self.color2, self.fonts, self.colors)
            self.dialog._editing_primary = False
            return
        # Zoom buttons
        for action, rect in self._get_zoom_buttons():
            if pygame.Rect(rect).collidepoint(mx, my):
                if action == "+": self.zoom = min(16.0, self.zoom * 1.5)
                elif action == "-": self.zoom = max(0.05, self.zoom / 1.5)
                elif action == "fit": self.zoom = 1.0; self._fit_canvas()
                return
        # Shape fill/outline toggles
        fill_rect, outline_rect = self._get_fill_outline_rects()
        if pygame.Rect(fill_rect).collidepoint(mx, my):
            self.shape_fill = not self.shape_fill
            return
        if pygame.Rect(outline_rect).collidepoint(mx, my):
            self.shape_outline = not self.shape_outline
            return

    def _handle_dropdown_click(self, mx, my):
        if not self.dropdown:
            return
        items = self._get_dropdown_items(self.dropdown[0])
        x, y = self.dropdown[1], self.dropdown[2]
        for i, (label, action) in enumerate(items):
            item_rect = pygame.Rect(x, y + i*30, 200, 30)
            if item_rect.collidepoint(mx, my):
                self.dropdown = None
                action()
                return
        self.dropdown = None

    def _in_dropdown(self, mx, my):
        if not self.dropdown:
            return False
        items = self._get_dropdown_items(self.dropdown[0])
        n = len(items)
        x, y = self.dropdown[1], self.dropdown[2]
        return pygame.Rect(x, y, 200, n*30+8).collidepoint(mx, my)

    # ── File operations ──────────────────────────────────────────────────────
    def _new_file(self):
        self.canvas = Canvas(900, 600)
        self.current_file = None
        self.title_modified = False
        self._fit_canvas()

    def load_image(self, path):
        """Load an image file into the canvas. Returns True on success."""
        if not path or not str(path).strip():
            return False
        path = str(path)
        if not os.path.exists(path):
            print(f"Could not open image: file not found: {path}")
            return False
        try:
            img = pygame.image.load(path)
            try:
                surf = img.convert_alpha()   # keep transparency (PNG)
            except Exception:
                surf = img.convert()
            w, h = surf.get_width(), surf.get_height()
            # Build a fresh canvas with the image on the background layer.
            # Background is turned OFF so any area the image doesn't cover —
            # or that you erase — shows the transparency grid (like W11 Paint
            # when an opened image has only one layer).
            self.canvas = Canvas(w, h)
            self.canvas.has_background = False
            base = self.canvas.layers[0]
            base.name = "Image"
            base.surface.fill((0, 0, 0, 0))
            base.surface.blit(surf, (0, 0))
            self.canvas.push_history()
            self.current_file = path
            self.title_modified = False
            pygame.display.set_caption(f"{os.path.basename(path)} - Paint")
            self._fit_canvas()
            return True
        except Exception as e:
            print(f"Could not open image: {path}\n  {e}")
            return False

    def _pick_open_path(self):
        """Show a native file-open dialog and return a path, or None."""
        import shutil, subprocess
        filters_zenity = ("--file-filter=Images | *.png *.jpg *.jpeg *.bmp "
                          "*.gif *.webp *.tga *.tif *.tiff")
        # 1) zenity (GNOME/most distros)
        if shutil.which("zenity"):
            try:
                out = subprocess.run(
                    ["zenity", "--file-selection", "--title=Open image",
                     filters_zenity],
                    capture_output=True, text=True, timeout=120)
                if out.returncode == 0:
                    return out.stdout.strip() or None
                return None
            except Exception:
                pass
        # 2) kdialog (KDE)
        if shutil.which("kdialog"):
            try:
                out = subprocess.run(
                    ["kdialog", "--getopenfilename", str(Path.home()),
                     "Images (*.png *.jpg *.jpeg *.bmp *.gif *.webp *.tga *.tif *.tiff)"],
                    capture_output=True, text=True, timeout=120)
                if out.returncode == 0:
                    return out.stdout.strip() or None
                return None
            except Exception:
                pass
        # 3) tkinter fallback (usually present with python)
        try:
            import tkinter as tk
            from tkinter import filedialog
            root = tk.Tk(); root.withdraw()
            p = filedialog.askopenfilename(
                title="Open image",
                filetypes=[("Images", "*.png *.jpg *.jpeg *.bmp *.gif "
                            "*.webp *.tga *.tif *.tiff"),
                           ("All files", "*.*")])
            root.destroy()
            return p or None
        except Exception:
            return None

    def _open_file(self):
        path = self._pick_open_path()
        if path:
            self.load_image(path)

    def _pick_save_path(self):
        """Show a native file-save dialog and return a path, or None."""
        import shutil, subprocess
        default = self.current_file or str(Path.home() / "untitled.png")
        if shutil.which("zenity"):
            try:
                out = subprocess.run(
                    ["zenity", "--file-selection", "--save",
                     "--confirm-overwrite", "--title=Save image",
                     f"--filename={default}"],
                    capture_output=True, text=True, timeout=120)
                if out.returncode == 0:
                    return out.stdout.strip() or None
                return None
            except Exception:
                pass
        if shutil.which("kdialog"):
            try:
                out = subprocess.run(
                    ["kdialog", "--getsavefilename", default,
                     "Images (*.png *.jpg *.jpeg *.bmp *.tga)"],
                    capture_output=True, text=True, timeout=120)
                if out.returncode == 0:
                    return out.stdout.strip() or None
                return None
            except Exception:
                pass
        try:
            import tkinter as tk
            from tkinter import filedialog
            root = tk.Tk(); root.withdraw()
            p = filedialog.asksaveasfilename(
                title="Save image", defaultextension=".png",
                initialfile=os.path.basename(default),
                filetypes=[("PNG", "*.png"), ("JPEG", "*.jpg"),
                           ("Bitmap", "*.bmp"), ("All files", "*.*")])
            root.destroy()
            return p or None
        except Exception:
            return None

    def _save_file(self, save_as=False):
        path = self.current_file
        if save_as or not path:
            path = self._pick_save_path()
            if not path:
                return  # user cancelled
        try:
            out = self.canvas.composite()
            # If saving to a non-PNG, drop alpha onto the bg colour
            ext = os.path.splitext(path)[1].lower()
            if ext not in (".png", ".webp", ".tga", ".tiff", ".tif"):
                flat = pygame.Surface((out.get_width(), out.get_height()))
                flat.fill(self.canvas.bg_color)
                flat.blit(out, (0, 0))
                out = flat
            pygame.image.save(out, path)
            self.current_file = path
            self.title_modified = False
            pygame.display.set_caption(f"{os.path.basename(path)} - Paint")
        except Exception as e:
            print(f"Could not save: {path}\n  {e}")

    def _copy_selection(self):
        if self.selection:
            sx,sy,sw,sh = self.selection
            r = pygame.Rect(sx,sy,sw,sh)
            self.selection_copy = self.canvas.surface.subsurface(r).copy()

    def _cut_selection(self):
        self._copy_selection()
        if self.selection:
            sx,sy,sw,sh = self.selection
            pygame.draw.rect(self.canvas.surface, self.color2, (sx,sy,sw,sh))
            self.canvas.push_history()

    def _paste(self):
        if self.selection_copy:
            w,h = self.selection_copy.get_size()
            self.canvas.surface.blit(self.selection_copy, (10,10))
            self.canvas.push_history()
            self.selection = (10,10,w,h)
            self.selection_active = True

    def _commit_text(self):
        if self.text_box and self.text_content:
            try:
                font = pygame.font.SysFont(self.text_font_name, self.text_font_size)
            except:
                font = self.fonts["ui"]
            s = font.render(self.text_content, True, self.color1)
            self.canvas.surface.blit(s, self.text_box)
            self.canvas.push_history()
        self.text_box = None
        self.text_content = ""

    # ── Layout helpers ───────────────────────────────────────────────────────
    def _get_menu_buttons(self):
        items = ["File", "Edit", "View", "Image"]
        result = {}
        x = 8
        for name in items:
            w = self.fonts["ui"].size(name)[0] + 20
            result[name] = (x, 8, w, 26)
            x += w + 2
        return result

    def _get_quick_actions(self):
        sw = self.SCREEN_W
        actions = []
        # Right side of title: undo, redo, save
        x = sw // 2 - 60
        for name in ("undo","redo","save"):
            actions.append((name, (x, 8, 28, 26)))
            x += 34
        return actions

    def _get_tool_buttons(self):
        # Returns [(name, rect)] for all toolbar tools
        TOOLS = [
            # Group 1: Selection
            ("select_rect", "Rectangular selection"),
            ("select_free", "Free-form selection"),
            None,  # separator
            # Group 2: View
            ("magnify", "Magnifier"),
            None,
            # Group 3: Drawing
            ("pencil", "Pencil"),
            ("fill", "Fill with color"),
            ("text", "Text"),
            ("eraser", "Eraser"),
            ("eyedropper", "Color picker"),
            ("brush", "Brushes"),
            None,
            # Group 4: Shapes
            ("line", "Line"),
            ("rect", "Rectangle"),
            ("ellipse", "Ellipse"),
            ("triangle", "Triangle"),
            ("rounded_rect", "Rounded rectangle"),
            None,
            # Group 5: Image
            ("resize", "Resize"),
            ("crop", "Crop"),
            ("rotate", "Rotate"),
            ("flip", "Flip"),
        ]
        ICON_SIZE = 20
        BTN_SIZE  = 40
        ICON_DRAW = {
            "select_rect": draw_icon_select_rect,
            "select_free": draw_icon_select_free,
            "magnify":     draw_icon_magnify,
            "pencil":      draw_icon_pencil,
            "fill":        draw_icon_fill,
            "text":        draw_icon_text,
            "eraser":      draw_icon_eraser,
            "eyedropper":  draw_icon_eyedropper,
            "brush":       draw_icon_brush,
            "line":        draw_icon_line,
            "rect":        draw_icon_rect_shape,
            "ellipse":     draw_icon_ellipse_shape,
            "triangle":    draw_icon_triangle,
            "rounded_rect":draw_icon_rect_shape,
            "resize":      draw_icon_resize,
            "crop":        draw_icon_crop,
            "rotate":      draw_icon_rotate,
            "flip":        draw_icon_flip_h,
        }
        result = []
        x = 8
        ty = self.TITLE_H + (self.TOOLBAR_H - BTN_SIZE) // 2
        for item in TOOLS:
            if item is None:
                x += 8
                continue
            name, _ = item
            result.append((name, (x, ty, BTN_SIZE, BTN_SIZE)))
            x += BTN_SIZE + 2
        self._tool_icon_draw = ICON_DRAW
        self._tool_btn_start_x = 8
        self._tool_label = {name: label for name, label in (t for t in TOOLS if t)}
        return result

    def _get_size_buttons(self):
        sizes = [1, 3, 5, 8]
        result = []
        x = self.SCREEN_W - 460
        ty = self.TITLE_H + 8
        for i, sz in enumerate(sizes):
            result.append((sz, (x, ty + i * 13, 50, 12)))
        return result

    def _get_palette_rects(self):
        rects = []
        sw_start = self.SCREEN_W - 400
        SWATCH = 18
        GAP    = 2
        cols   = 14
        tx = self.TITLE_H + (self.TOOLBAR_H - SWATCH*2 - GAP) // 2
        for i in range(len(self.palette)):
            row = i // cols
            col = i % cols
            x = sw_start + col * (SWATCH + GAP)
            y = tx + row * (SWATCH + GAP)
            rects.append((x, y, SWATCH, SWATCH))
        return rects

    def _get_color_circles(self):
        # Large color circles at end of toolbar
        cx = self.SCREEN_W - 80
        cy = self.TITLE_H + self.TOOLBAR_H // 2
        c1 = (cx - 10, cy - 18, 26, 26)  # primary (top-left)
        c2 = (cx + 4,  cy - 6,  26, 26)  # secondary (bottom-right)
        return c1, c2

    def _get_zoom_buttons(self):
        x = self.SCREEN_W - 180
        ty = self.TITLE_H + (self.TOOLBAR_H - 28) // 2
        return [
            ("-", (x,   ty, 28, 28)),
            ("fit",(x+32, ty, 50, 28)),
            ("+", (x+86, ty, 28, 28)),
        ]

    def _get_fill_outline_rects(self):
        # Near shape tools
        x = self.SCREEN_W - 290
        ty = self.TITLE_H + 10
        return (x, ty, 60, 20), (x, ty+24, 60, 20)

    def _get_dropdown_items(self, menu):
        if menu == "File":
            return [
                ("New",       self._new_file),
                ("Open...",   self._open_file),
                ("Save",      lambda: self._save_file(False)),
                ("Save As...",lambda: self._save_file(True)),
                ("─────────", lambda: None),
                ("Exit",      lambda: pygame.event.post(pygame.event.Event(pygame.QUIT))),
            ]
        elif menu == "Edit":
            return [
                ("Undo  Ctrl+Z",   self.canvas.undo),
                ("Redo  Ctrl+Y",   self.canvas.redo),
                ("─────────", lambda: None),
                ("Select All Ctrl+A", lambda: None),
                ("Cut   Ctrl+X",   self._cut_selection),
                ("Copy  Ctrl+C",   self._copy_selection),
                ("Paste Ctrl+V",   self._paste),
            ]
        elif menu == "View":
            return [
                ("Zoom In  Ctrl++",  lambda: setattr(self, 'zoom', min(16.0, self.zoom*1.5))),
                ("Zoom Out Ctrl+-",  lambda: setattr(self, 'zoom', max(0.05, self.zoom/1.5))),
                ("Zoom 100%  Ctrl+0",lambda: (setattr(self, 'zoom', 1.0), self._fit_canvas())),
                ("─────────", lambda: None),
                ("Toggle Grid",      lambda: setattr(self, 'show_grid', not self.show_grid)),
                ("Toggle Rulers",    lambda: setattr(self, 'show_rulers', not self.show_rulers)),
                ("Toggle Dark Mode  Ctrl+D", self.toggle_theme),
            ]
        elif menu == "Image":
            return [
                ("Resize...",        lambda: setattr(self, 'dialog',
                    ResizeDialog(self.SCREEN_W, self.SCREEN_H,
                                 self.canvas.width, self.canvas.height,
                                 self.fonts, self.colors))),
                ("Rotate 90° CW",   self._rotate_canvas),
                ("Flip Horizontal", self._flip_h),
                ("Flip Vertical",   self._flip_v),
                ("─────────", lambda: None),
                ("Clear Canvas",    self.canvas.clear),
            ]
        return []

    def _rotate_canvas(self):
        for lyr in self.canvas.layers:
            lyr.surface = pygame.transform.rotate(lyr.surface, -90)
        self.canvas.width, self.canvas.height = self.canvas.layers[0].surface.get_size()
        self.canvas.push_history()
        self._fit_canvas()

    def _flip_h(self):
        for lyr in self.canvas.layers:
            lyr.surface = pygame.transform.flip(lyr.surface, True, False)
        self.canvas.push_history()

    def _flip_v(self):
        for lyr in self.canvas.layers:
            lyr.surface = pygame.transform.flip(lyr.surface, False, True)
        self.canvas.push_history()

    def _crop_to_selection(self):
        """Crop the canvas to the current rectangular selection."""
        if not (self.selection_active and self.selection):
            return
        sx, sy, sw, sh = self.selection
        sx, sy = max(0, sx), max(0, sy)
        sw = min(sw, self.canvas.width - sx)
        sh = min(sh, self.canvas.height - sy)
        if sw <= 0 or sh <= 0:
            return
        for lyr in self.canvas.layers:
            new_s = pygame.Surface((sw, sh), pygame.SRCALPHA)
            new_s.blit(lyr.surface, (0, 0), pygame.Rect(sx, sy, sw, sh))
            lyr.surface = new_s
        self.canvas.width, self.canvas.height = sw, sh
        self.selection = None
        self.selection_active = False
        self.canvas.push_history()
        self._fit_canvas()

    def _update_toolbar_tooltip(self, mx, my):
        for name, rect in self._get_tool_buttons():
            if pygame.Rect(rect).collidepoint(mx, my):
                label = getattr(self, '_tool_label', {}).get(name, name)
                self.tooltip.set(label, rect)
                return

    # ══════════════════════════════════════════════════════════════════════════
    # Rendering
    # ══════════════════════════════════════════════════════════════════════════
    def render(self):
        c = self.colors
        surf = self.screen

        # ── Background ──────────────────────────────────────────────────────
        surf.fill(c["bg"])

        # ── Canvas area ──────────────────────────────────────────────────────
        ca = self.canvas_area
        pygame.draw.rect(surf, c["canvas_bg"], ca)

        # Canvas shadow
        cw = int(self.canvas.width * self.zoom)
        ch = int(self.canvas.height * self.zoom)
        cx = ca.x + self.scroll_x
        cy = ca.y + self.scroll_y
        shadow_rect = pygame.Rect(cx+3, cy+3, cw, ch)
        pygame.draw.rect(surf, c["shadow"], shadow_rect)

        # Composite all visible layers into one image for display
        composite = self.canvas.composite()

        # Draw preview for shape tools (onto a copy of the active layer,
        # then re-composite so the preview shows above lower layers)
        if self.drawing and self.tool in ("line","rect","ellipse","triangle","rounded_rect") and self.start_pos:
            mx, my = pygame.mouse.get_pos()
            ecx, ecy = self.screen_to_canvas(mx, my)
            color = self.color1 if self._drawing_with_left else self.color2
            active_copy = self.canvas.surface.copy()
            self._draw_shape_preview(active_copy, self.start_pos, (ecx, ecy), color, self.tool)
            composite = pygame.Surface((self.canvas.width, self.canvas.height), pygame.SRCALPHA)
            composite.fill((*self.canvas.bg_color, 255))
            composite = pygame.Surface((self.canvas.width, self.canvas.height), pygame.SRCALPHA)
            if self.canvas.has_background:
                composite.fill((*self.canvas.bg_color, 255))
            else:
                composite.fill((0, 0, 0, 0))
            for li, lyr in enumerate(self.canvas.layers):
                if lyr.visible:
                    composite.blit(active_copy if li == self.canvas.active_idx else lyr.surface, (0, 0))

        # If the canvas has no background, paint the transparency checkerboard
        # underneath so see-through areas read as "nothing here" (W11 style).
        if not self.canvas.has_background:
            self._draw_checkerboard(surf, cx, cy, cw, ch)

        # Canvas surface (scaled)
        if self.zoom != 1.0:
            scaled = pygame.transform.scale(composite, (cw, ch))
        else:
            scaled = composite

        surf.blit(scaled, (cx, cy))

        # Grid
        if self.show_grid and self.zoom >= 4:
            grid_color = (200, 200, 220, 80)
            step = max(1, int(self.zoom))
            for gx in range(0, cw, step):
                pygame.draw.line(surf, (190,190,210), (cx+gx, cy), (cx+gx, cy+ch), 1)
            for gy in range(0, ch, step):
                pygame.draw.line(surf, (190,190,210), (cx, cy+gy), (cx+cw, cy+gy), 1)

        # Canvas border
        pygame.draw.rect(surf, c["border"], (cx, cy, cw, ch), 1)

        # Freeform selection preview
        if self.tool == "select_free" and self.drawing and len(self.freeform_points) > 1:
            pts = [self.canvas_to_screen(p[0],p[1]) for p in self.freeform_points]
            pygame.draw.lines(surf, c["accent"], False, pts, 1)

        # Rectangular selection preview
        if self.tool == "select_rect" and self.drawing and self.start_pos:
            mx, my = pygame.mouse.get_pos()
            ecx, ecy = self.screen_to_canvas(mx, my)
            sx = min(self.start_pos[0], ecx)
            sy = min(self.start_pos[1], ecy)
            sw = abs(ecx - self.start_pos[0])
            sh = abs(ecy - self.start_pos[1])
            sx_s, sy_s = self.canvas_to_screen(sx, sy)
            sw_s = int(sw * self.zoom)
            sh_s = int(sh * self.zoom)
            # Marching ants
            t = (pygame.time.get_ticks() // 100) % 8
            for i in range(0, max(sw_s, sh_s, 1), 8):
                off = (i + t) % 16
                draw_color = c["accent"] if off < 8 else c["white"]
                if i < sw_s:
                    pygame.draw.rect(surf, draw_color, (sx_s+i, sy_s, min(8, sw_s-i), 1))
                    pygame.draw.rect(surf, draw_color, (sx_s+i, sy_s+sh_s, min(8, sw_s-i), 1))
                if i < sh_s:
                    pygame.draw.rect(surf, draw_color, (sx_s, sy_s+i, 1, min(8, sh_s-i)))
                    pygame.draw.rect(surf, draw_color, (sx_s+sw_s, sy_s+i, 1, min(8, sh_s-i)))

        # Active selection (marching ants)
        if self.selection_active and self.selection:
            sx,sy,sw,sh = self.selection
            sx_s, sy_s = self.canvas_to_screen(sx, sy)
            sw_s = int(sw * self.zoom)
            sh_s = int(sh * self.zoom)
            t = (pygame.time.get_ticks() // 100) % 16
            for i in range(0, max(sw_s, sh_s, 1), 8):
                off = (i + t) % 16
                dc = c["accent"] if off < 8 else c["white"]
                if i < sw_s:
                    pygame.draw.rect(surf, dc, (sx_s+i, sy_s, min(8, sw_s-i), 1))
                    pygame.draw.rect(surf, dc, (sx_s+i, sy_s+sh_s, min(8, sw_s-i), 1))
                if i < sh_s:
                    pygame.draw.rect(surf, dc, (sx_s, sy_s+i, 1, min(8, sh_s-i)))
                    pygame.draw.rect(surf, dc, (sx_s+sw_s, sy_s+i, 1, min(8, sh_s-i)))

        # Text cursor preview
        if self.tool == "text" and self.text_box:
            try:
                tfont = pygame.font.SysFont(self.text_font_name, int(self.text_font_size * self.zoom))
            except:
                tfont = self.fonts["ui"]
            display_text = self.text_content
            if (pygame.time.get_ticks() // 500) % 2 == 0:
                display_text += "|"
            s = tfont.render(display_text, True, self.color1)
            tx_s, ty_s = self.canvas_to_screen(*self.text_box)
            surf.blit(s, (tx_s, ty_s))

        # Rulers
        if self.show_rulers:
            self._draw_rulers(surf)

        # Layers panel
        self._draw_layer_panel(surf)

        # ── Title bar ────────────────────────────────────────────────────────
        pygame.draw.rect(surf, c["titlebar"], self.title_rect)
        pygame.draw.line(surf, c["border"], (0, self.TITLE_H-1), (self.SCREEN_W, self.TITLE_H-1), 1)

        # App icon
        pygame.draw.rect(surf, c["accent"], (8, 10, 22, 22), border_radius=4)
        draw_text_centered(surf, "P", self.fonts["ui_med"], c["white"], (8, 10, 22, 22))

        # App title
        title = "Paint"
        if self.current_file:
            title = Path(self.current_file).name + " - Paint"
        if self.title_modified:
            title = "* " + title
        draw_text(surf, title, self.fonts["ui_med"], c["text"], 36, 14)

        # Menu buttons
        mx_cur, my_cur = pygame.mouse.get_pos()
        for name, rect in self._get_menu_buttons().items():
            is_open = self.dropdown and self.dropdown[0] == name
            hov = pygame.Rect(rect).collidepoint(mx_cur, my_cur)
            if is_open:
                draw_rounded_rect(surf, c["btn_active"], rect, 4)
            elif hov:
                draw_rounded_rect(surf, c["btn_hover"], rect, 4)
            draw_text_centered(surf, name, self.fonts["ui"], c["text"], rect)

        # Quick actions: undo, redo, save
        for name, rect in self._get_quick_actions():
            hov = pygame.Rect(rect).collidepoint(mx_cur, my_cur)
            if hov:
                draw_rounded_rect(surf, c["btn_hover"], rect, 4)
            icon_color = c["text"] if (
                (name == "undo" and self.canvas.can_undo()) or
                (name == "redo" and self.canvas.can_redo()) or
                name == "save"
            ) else c["text_sec"]
            ix = rect[0] + (rect[2] - 16)//2
            iy = rect[1] + (rect[3] - 16)//2
            if name == "undo":   draw_icon_undo(surf, icon_color, ix, iy)
            elif name == "redo": draw_icon_redo(surf, icon_color, ix, iy)
            elif name == "save": draw_icon_save(surf, icon_color, ix, iy)

        # Window controls (min/max/close) — top right
        wc_x = self.SCREEN_W - 140
        for i, (label, col, hov_col) in enumerate([
            ("─", c["btn_hover"], c["btn_hover"]),
            ("□", c["btn_hover"], c["btn_hover"]),
            ("✕", (196,43,28),    (196,43,28)),
        ]):
            r = (wc_x + i*46, 0, 46, self.TITLE_H)
            hov = pygame.Rect(r).collidepoint(mx_cur, my_cur)
            if hov:
                bg = hov_col if i < 2 else (232,17,35)
                draw_rounded_rect(surf, bg, r, 0)
            fc = c["white"] if (hov and i == 2) else c["text"]
            draw_text_centered(surf, label, self.fonts["ui_lg"], fc, r)

        # ── Toolbar ──────────────────────────────────────────────────────────
        pygame.draw.rect(surf, c["toolbar_bg"], self.toolbar_rect)
        pygame.draw.line(surf, c["border"], (0, self.TITLE_H + self.TOOLBAR_H - 1),
                         (self.SCREEN_W, self.TITLE_H + self.TOOLBAR_H - 1), 1)
        pygame.draw.line(surf, c["border"], (0, self.TITLE_H),
                         (self.SCREEN_W, self.TITLE_H), 1)

        # Tool buttons
        ICON_SIZE = 16
        for name, rect in self._get_tool_buttons():
            is_active = self.tool == name
            hov = pygame.Rect(rect).collidepoint(mx_cur, my_cur)
            if is_active:
                draw_rounded_rect(surf, c["btn_active"], rect, 6)
                pygame.draw.rect(surf, c["accent"], (rect[0], rect[1]+rect[3]-2, rect[2], 2), border_radius=1)
            elif hov:
                draw_rounded_rect(surf, c["btn_hover"], rect, 6)
            icon_color = c["accent"] if is_active else c["text"]
            icon_fn = getattr(self, '_tool_icon_draw', {}).get(name)
            if icon_fn:
                ix = rect[0] + (rect[2] - ICON_SIZE)//2
                iy = rect[1] + (rect[3] - ICON_SIZE)//2
                icon_fn(surf, icon_color, ix, iy, ICON_SIZE)

        # Section separators (subtle vertical lines)
        sep_positions = []
        prev_sep = 8
        TOOLS_ORDER = [
            "select_rect","select_free",None,"magnify",None,
            "pencil","fill","text","eraser","eyedropper","brush",None,
            "line","rect","ellipse","triangle","rounded_rect",None,
            "resize","crop","rotate","flip"
        ]
        x = 8
        for item in TOOLS_ORDER:
            if item is None:
                sep_positions.append(x + 4)
                x += 8
            else:
                x += 42
        for sx2 in sep_positions:
            ty = self.TITLE_H + 12
            pygame.draw.line(surf, c["separator"],
                             (sx2, ty), (sx2, ty + self.TOOLBAR_H - 24), 1)

        # Brush size indicators (left of palette)
        bsize_x = self.SCREEN_W - 470
        draw_text(surf, "Size", self.fonts["ui_sm"], c["text_sec"], bsize_x, self.TITLE_H + 8)
        sizes = [1, 3, 5, 8]
        for i, sz in enumerate(sizes):
            is_sel = self.brush_size == sz
            rect_y = self.TITLE_H + 22 + i * 10
            # Dot preview
            r = pygame.Rect(bsize_x, rect_y + 1, 60, 8)
            if is_sel:
                draw_rounded_rect(surf, c["btn_active"], r, 3)
            dot_r = sz // 2 + 1
            pygame.draw.circle(surf, c["text"] if not is_sel else c["accent"],
                                (bsize_x + 30, rect_y + 5), dot_r)

        # Size slider (horizontal)
        slider_x = self.SCREEN_W - 470
        slider_y = self.TITLE_H + self.TOOLBAR_H - 16
        slider_w = 60
        draw_text(surf, f"{self.brush_size}px", self.fonts["ui_sm"], c["text_sec"],
                  slider_x + 64, slider_y - 2)

        # Shape fill/outline toggles
        fill_rect, outline_rect = self._get_fill_outline_rects()
        for label, rect, active in [
            ("Fill",    fill_rect,    self.shape_fill),
            ("Outline", outline_rect, self.shape_outline),
        ]:
            hov = pygame.Rect(rect).collidepoint(mx_cur, my_cur)
            if active:
                draw_rounded_rect(surf, c["btn_active"], rect, 4)
            elif hov:
                draw_rounded_rect(surf, c["btn_hover"], rect, 4)
            else:
                draw_rounded_rect(surf, c["toolbar_bg"], rect, 4, 1, c["border"])
            draw_text_centered(surf, label, self.fonts["ui_sm"], c["text"], rect)

        # Zoom buttons
        for action, rect in self._get_zoom_buttons():
            hov = pygame.Rect(rect).collidepoint(mx_cur, my_cur)
            bg = c["btn_hover"] if hov else c["toolbar_bg"]
            draw_rounded_rect(surf, bg, rect, 4, 1, c["border"])
            if action == "fit":
                draw_text_centered(surf, f"{int(self.zoom*100)}%", self.fonts["ui_sm"], c["text"], rect)
            else:
                draw_text_centered(surf, action, self.fonts["ui_lg"], c["text"], rect)

        # Color palette
        for i, rect in enumerate(self._get_palette_rects()):
            if i < len(self.palette):
                col = self.palette[i]
                draw_rounded_rect(surf, col, rect, 3, 1, c["color_border"])
                hov = pygame.Rect(rect).collidepoint(mx_cur, my_cur)
                if hov:
                    pygame.draw.rect(surf, c["accent"], rect, 2, border_radius=3)

        # Primary/secondary color circles
        c1_rect, c2_rect = self._get_color_circles()
        # Shadow circle (bg) for depth
        draw_rounded_rect(surf, c["border"], (c2_rect[0]-1, c2_rect[1]-1,
                           c2_rect[2]+2, c2_rect[3]+2), 14)
        draw_rounded_rect(surf, self.color2, c2_rect, 13)
        pygame.draw.rect(surf, c["border"], c2_rect, 1, border_radius=13)

        draw_rounded_rect(surf, c["border"], (c1_rect[0]-1, c1_rect[1]-1,
                           c1_rect[2]+2, c1_rect[3]+2), 14)
        draw_rounded_rect(surf, self.color1, c1_rect, 13)
        pygame.draw.rect(surf, c["border"], c1_rect, 1, border_radius=13)

        # Labels
        draw_text(surf, "Colors", self.fonts["ui_sm"], c["text_sec"],
                  self.SCREEN_W - 80, self.TITLE_H + 50)

        # ── Status bar ───────────────────────────────────────────────────────
        pygame.draw.rect(surf, c["statusbar"], self.statusbar_rect)
        pygame.draw.line(surf, c["statusbar_brd"],
                         (0, self.statusbar_rect.y),
                         (self.SCREEN_W, self.statusbar_rect.y), 1)

        mx_c, my_c = pygame.mouse.get_pos()
        if self.canvas_area.collidepoint(mx_c, my_c):
            cx2, cy2 = self.screen_to_canvas(mx_c, my_c)
            pos_text = f"  {cx2}, {cy2}px"
        else:
            pos_text = ""
        size_text = f"  {self.canvas.width} × {self.canvas.height}px"
        zoom_text = f"  {int(self.zoom*100)}%"
        sel_text  = ""
        if self.selection_active and self.selection:
            sx,sy,sw,sh = self.selection
            sel_text = f"  Selection: {sw}×{sh}"

        sy_sb = self.statusbar_rect.y + 5
        draw_text(surf, pos_text, self.fonts["ui_sm"], c["text_sec"], 8, sy_sb)
        # Separator
        pygame.draw.line(surf, c["border"], (120, sy_sb), (120, sy_sb+14), 1)
        draw_text(surf, size_text, self.fonts["ui_sm"], c["text_sec"], 124, sy_sb)
        pygame.draw.line(surf, c["border"], (280, sy_sb), (280, sy_sb+14), 1)
        draw_text(surf, zoom_text, self.fonts["ui_sm"], c["text_sec"], 284, sy_sb)
        if sel_text:
            pygame.draw.line(surf, c["border"], (340, sy_sb), (340, sy_sb+14), 1)
            draw_text(surf, sel_text, self.fonts["ui_sm"], c["text_sec"], 344, sy_sb)

        # Canvas dimensions display (right side)
        cr_txt = f"{self.canvas.width} × {self.canvas.height}"
        cr_s = self.fonts["ui_sm"].render(cr_txt, True, c["text_sec"])
        surf.blit(cr_s, (self.SCREEN_W - cr_s.get_width() - 12, sy_sb))

        # ── Dropdown ────────────────────────────────────────────────────────
        if self.dropdown:
            name, dx, dy = self.dropdown
            items = self._get_dropdown_items(name)
            n = len(items)
            dw = 220
            dh = n * 30 + 8
            # Shadow
            shadow = pygame.Surface((dw+4, dh+4), pygame.SRCALPHA)
            shadow.fill((0,0,0,40))
            surf.blit(shadow, (dx+2, dy+2))
            draw_rounded_rect(surf, c["dropdown_bg"], (dx, dy, dw, dh), 6, 1, c["dropdown_brd"])
            for i, (label, _) in enumerate(items):
                ir = (dx+4, dy+4+i*30, dw-8, 28)
                hov = pygame.Rect(ir).collidepoint(mx_cur, my_cur)
                if hov:
                    draw_rounded_rect(surf, c["btn_hover"], ir, 4)
                is_sep = label.startswith("─")
                if is_sep:
                    pygame.draw.line(surf, c["separator"],
                                     (dx+8, dy+4+i*30+14), (dx+dw-8, dy+4+i*30+14), 1)
                else:
                    draw_text(surf, label, self.fonts["ui"], c["text"], ir[0]+8, ir[1]+7)

        # ── Dialog ──────────────────────────────────────────────────────────
        if self.dialog:
            # Dim background
            overlay = pygame.Surface((self.SCREEN_W, self.SCREEN_H), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 80))
            surf.blit(overlay, (0, 0))
            self.dialog.draw(surf)

        # ── Tooltip ─────────────────────────────────────────────────────────
        self.tooltip.update()
        self.tooltip.draw(surf, self.fonts, self.colors)

        # ── Cursor ──────────────────────────────────────────────────────────
        mx_c, my_c = pygame.mouse.get_pos()
        if self.canvas_area.collidepoint(mx_c, my_c):
            if self.tool in ("pencil","brush"):
                sz = max(2, self.brush_size if self.tool=="pencil" else self.brush_size*2)
                pygame.draw.circle(surf, (100,100,100),
                                   (mx_c, my_c), int(sz*self.zoom/2)+1, 1)
            elif self.tool == "eraser":
                sz = max(4, self.brush_size*4)
                r = pygame.Rect(mx_c-sz//2, my_c-sz//2, sz, sz)
                pygame.draw.rect(surf, (100,100,100), r, 1)
            elif self.tool == "eyedropper":
                pygame.draw.circle(surf, c["accent"], (mx_c, my_c), 6, 2)

        pygame.display.flip()

    def _layer_row_rects(self):
        """Return list of (idx, row_rect, eye_rect) top layer first."""
        rects = []
        if not self.layers_panel_open:
            return rects
        p = self.layer_panel_rect
        row_h = 44
        top = p.y + 84  # below header + add button
        n = len(self.canvas.layers)
        # Top layer drawn first (reverse order)
        for vi, idx in enumerate(range(n - 1, -1, -1)):
            ry = top + vi * (row_h + 4)
            row = pygame.Rect(p.x + 8, ry, p.width - 16, row_h)
            eye = pygame.Rect(row.right - 32, ry + row_h//2 - 9, 18, 18)
            rects.append((idx, row, eye))
        return rects

    def _layer_panel_buttons(self):
        p = self.layer_panel_rect
        add = pygame.Rect(p.x + 8, p.y + 44, 32, 30)
        dup = pygame.Rect(p.x + 44, p.y + 44, 32, 30)
        dele = pygame.Rect(p.x + 80, p.y + 44, 32, 30)
        up  = pygame.Rect(p.x + 116, p.y + 44, 32, 30)
        down = pygame.Rect(p.x + 152, p.y + 44, 32, 30)
        return {"add": add, "dup": dup, "del": dele, "up": up, "down": down}

    def _handle_layer_panel_click(self, mx, my):
        if not self.layers_panel_open or not self.layer_panel_rect.collidepoint(mx, my):
            return False
        btns = self._layer_panel_buttons()
        if btns["add"].collidepoint(mx, my):
            self.canvas.add_layer(); return True
        if btns["dup"].collidepoint(mx, my):
            self.canvas.duplicate_layer(); return True
        if btns["del"].collidepoint(mx, my):
            self.canvas.delete_layer(); return True
        if btns["up"].collidepoint(mx, my):
            self.canvas.move_layer(self.canvas.active_idx, +1); return True
        if btns["down"].collidepoint(mx, my):
            self.canvas.move_layer(self.canvas.active_idx, -1); return True
        # Background on/off toggle
        if self._bg_toggle_rect().collidepoint(mx, my):
            self.canvas.toggle_background(); return True
        for idx, row, eye in self._layer_row_rects():
            if eye.collidepoint(mx, my):
                self.canvas.toggle_visible(idx); return True
            if row.collidepoint(mx, my):
                self.canvas.select_layer(idx); return True
        return True  # click was inside panel, swallow it

    def _draw_checkerboard(self, surf, cx, cy, cw, ch):
        """Gray/white checker pattern shown through transparent areas."""
        tile = 8
        light = (255, 255, 255)
        dark = (204, 204, 204)
        clip = surf.get_clip()
        surf.set_clip(pygame.Rect(cx, cy, cw, ch))
        for yy in range(0, ch, tile):
            for xx in range(0, cw, tile):
                color = light if ((xx // tile + yy // tile) % 2 == 0) else dark
                pygame.draw.rect(surf, color, (cx + xx, cy + yy, tile, tile))
        surf.set_clip(clip)

    def toggle_theme(self):
        self.theme = "light" if self.theme == "dark" else "dark"
        self.colors = THEMES[self.theme]

    def toggle_layers_panel(self):
        self.layers_panel_open = not self.layers_panel_open
        self._calc_layout()

    def _draw_layer_panel(self, surf):
        if not self.layers_panel_open:
            return
        c = self.colors
        p = self.layer_panel_rect
        pygame.draw.rect(surf, c["toolbar_bg"], p)
        pygame.draw.line(surf, c["border"], (p.x, p.y), (p.x, p.bottom), 1)
        draw_text(surf, "Layers", self.fonts["ui_med"], c["text"], p.x + 12, p.y + 12)

        mx, my = pygame.mouse.get_pos()
        # Toolbar buttons
        btns = self._layer_panel_buttons()
        labels = {"add": "+", "dup": "⧉", "del": "🗑", "up": "▲", "down": "▼"}
        for key, r in btns.items():
            hov = r.collidepoint(mx, my)
            draw_rounded_rect(surf, c["btn_hover"] if hov else c["white"], r, 4, 1, c["border"])
            draw_text_centered(surf, labels[key], self.fonts["ui"], c["text"], r)

        # Layer rows (top layer first)
        for idx, row, eye in self._layer_row_rects():
            lyr = self.canvas.layers[idx]
            active = (idx == self.canvas.active_idx)
            draw_rounded_rect(surf, c["btn_active"] if active else c["white"],
                              row, 4, 2 if active else 1,
                              c["accent"] if active else c["border"])
            # thumbnail
            th = pygame.Rect(row.x + 6, row.y + 6, 32, 32)
            pygame.draw.rect(surf, c["white"], th)
            try:
                thumb = pygame.transform.smoothscale(lyr.surface, (32, 32))
                surf.blit(thumb, th.topleft)
            except Exception:
                pass
            pygame.draw.rect(surf, c["border"], th, 1)
            draw_text(surf, lyr.name, self.fonts["ui"], c["text"], row.x + 46, row.y + 13)
            # eye / hidden icon
            col = c["text"] if lyr.visible else c["text_sec"]
            pygame.draw.ellipse(surf, col, (eye.x, eye.y+4, 18, 10), 1)
            pygame.draw.circle(surf, col, (eye.x+9, eye.y+9), 3)
            if not lyr.visible:
                pygame.draw.line(surf, c["text_sec"], (eye.x, eye.bottom),
                                 (eye.right, eye.y), 2)

        # Canvas background toggle at the bottom of the panel
        bg_rect = self._bg_toggle_rect()
        label = "Background: ON" if self.canvas.has_background else "Background: OFF (transparent)"
        draw_text(surf, "Canvas", self.fonts["ui_sm"], c["text_sec"], bg_rect.x, bg_rect.y - 18)
        hov = bg_rect.collidepoint(mx, my)
        draw_rounded_rect(surf, c["btn_hover"] if hov else c["white"], bg_rect, 4, 1, c["border"])
        # little swatch: white square if ON, checker if OFF
        sw_box = pygame.Rect(bg_rect.x + 6, bg_rect.y + 6, bg_rect.height - 12, bg_rect.height - 12)
        if self.canvas.has_background:
            pygame.draw.rect(surf, self.canvas.bg_color, sw_box)
        else:
            t = 5
            for j in range(0, sw_box.h, t):
                for i in range(0, sw_box.w, t):
                    col = (255,255,255) if ((i//t + j//t) % 2 == 0) else (204,204,204)
                    pygame.draw.rect(surf, col, (sw_box.x+i, sw_box.y+j, t, t))
        pygame.draw.rect(surf, c["border"], sw_box, 1)
        draw_text(surf, label, self.fonts["ui_sm"], c["text"], sw_box.right + 8, bg_rect.y + 8)

    def _bg_toggle_rect(self):
        p = self.layer_panel_rect
        return pygame.Rect(p.x + 8, p.bottom - 40, p.width - 16, 30)

    def _draw_rulers(self, surf):
        c = self.colors
        RULER_SIZE = 18
        ca = self.canvas_area

        # Horizontal ruler
        h_ruler = pygame.Rect(ca.x, ca.y, ca.width, RULER_SIZE)
        pygame.draw.rect(surf, c["toolbar_bg"], h_ruler)
        pygame.draw.line(surf, c["border"], (ca.x, ca.y+RULER_SIZE-1),
                         (ca.x+ca.width, ca.y+RULER_SIZE-1), 1)

        # Vertical ruler  
        v_ruler = pygame.Rect(ca.x, ca.y+RULER_SIZE, RULER_SIZE, ca.height-RULER_SIZE)
        pygame.draw.rect(surf, c["toolbar_bg"], v_ruler)
        pygame.draw.line(surf, c["border"], (ca.x+RULER_SIZE-1, ca.y+RULER_SIZE),
                         (ca.x+RULER_SIZE-1, ca.y+ca.height), 1)

        # Ruler marks
        step = 50  # pixels on canvas
        screen_step = int(step * self.zoom)
        if screen_step < 4:
            return
        cx0 = ca.x + self.scroll_x
        cy0 = ca.y + RULER_SIZE + self.scroll_y
        font_sm = self.fonts["ui_sm"]

        # Horizontal ticks
        for px in range(0, self.canvas.width + step, step):
            sx = int(cx0 + px * self.zoom)
            if ca.x <= sx <= ca.x + ca.width:
                pygame.draw.line(surf, c["text_sec"],
                                 (sx, ca.y + RULER_SIZE - 8),
                                 (sx, ca.y + RULER_SIZE - 1), 1)
                if screen_step >= 30:
                    lbl = font_sm.render(str(px), True, c["text_sec"])
                    surf.blit(lbl, (sx+2, ca.y+3))

        # Vertical ticks
        for py in range(0, self.canvas.height + step, step):
            sy = int(cy0 + py * self.zoom)
            if ca.y + RULER_SIZE <= sy <= ca.y + ca.height:
                pygame.draw.line(surf, c["text_sec"],
                                 (ca.x + RULER_SIZE - 8, sy),
                                 (ca.x + RULER_SIZE - 1, sy), 1)
                if screen_step >= 30:
                    lbl = font_sm.render(str(py), True, c["text_sec"])
                    surf.blit(lbl, (ca.x+2, sy+2))

    # ══════════════════════════════════════════════════════════════════════════
    # Main loop
    # ══════════════════════════════════════════════════════════════════════════
    def run(self):
        self._drawing_with_left = True
        self._prev_tool = "pencil"
        running = True
        while running:
            self.clock.tick(60)
            running = self.handle_events()
            self.render()
        pygame.quit()
        sys.exit(0)


if __name__ == "__main__":
    open_path = None
    if len(sys.argv) > 1 and os.path.exists(sys.argv[1]):
        open_path = sys.argv[1]
    app = PaintApp(open_path=open_path)
    app.run()
