"""
Colors, fonts, and small generic drawing helpers used across the app.
Split out of the original paint11.py so theme/color tweaks don't require
touching the rest of the app.
"""
import pygame

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
