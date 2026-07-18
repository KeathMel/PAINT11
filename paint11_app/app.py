"""
PaintApp — the main window, event loop, toolbar, canvas rendering, and all
tool behavior. This is the one big module left after splitting out theme
colors (theme.py), toolbar icons (icons.py), the Layer/Canvas data model
(model.py), the small standalone dialogs (widgets.py), and native file
dialogs (native_dialogs.py). Those five hold the pieces that are easy to
touch in isolation; this file is the app logic that ties them together.
"""
import pygame
import pygame.gfxdraw
import sys
import os
import time
from pathlib import Path

from .theme import *
from .icons import *
from .model import Layer, Canvas
from .widgets import Tooltip, ResizeDialog, ColorPickerDialog
from .native_dialogs import spawn_open_dialog, spawn_save_dialog

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
        self._pending_file_op = None   # background open/save dialog, if any
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
        self._move_candidate = None
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
            if self.canvas.has_background and self.canvas.active_idx == 0:
                # Erasing the background layer of a normal (non-transparent)
                # canvas should reveal the background colour, like erasing
                # on paper — not punch a see-through hole in it.
                self.canvas.surface.fill((*self.canvas.bg_color, 255), r)
            else:
                # Any other layer is transparent by nature, so erasing it
                # should expose whatever's beneath, not a solid colour.
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
                            # Arm a move candidate only — don't touch the
                            # canvas yet. The punch-and-copy (which is what
                            # makes the selection area go blank) only
                            # happens once _handle_mouse_move confirms an
                            # actual drag past a small threshold. A plain
                            # click, or the sub-pixel jitter every real
                            # mouse produces, now does nothing at all.
                            self._move_candidate = {
                                "origin": (sx, sy),
                                "size": (sw2, sh2),
                                "start": (cx, cy),
                            }
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

        if getattr(self, "_move_candidate", None):
            # Clicked on the selection but never dragged past the
            # threshold — nothing was ever touched, just drop it.
            self._move_candidate = None
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

        # A selection move is "armed" but not yet started — only actually
        # begin it (punch the hole, grab the copy) once the mouse has
        # traveled a few real pixels from the click point. This is what
        # stops a plain click (or the sub-pixel jitter every mouse makes)
        # from ever visibly disturbing the selection.
        DRAG_THRESHOLD = 3
        cand = getattr(self, "_move_candidate", None)
        if cand and not self.selection_moving:
            dx = cx - cand["start"][0]
            dy = cy - cand["start"][1]
            if abs(dx) < DRAG_THRESHOLD and abs(dy) < DRAG_THRESHOLD:
                return  # not a real drag yet — canvas untouched
            sx, sy = cand["origin"]
            sw2, sh2 = cand["size"]
            self.selection_moving = True
            self.sel_move_start = cand["start"]
            self._sel_origin = (sx, sy)
            self.canvas.push_history()
            self.selection_copy = self.canvas.surface.subsurface(
                pygame.Rect(sx, sy, sw2, sh2)).copy()
            self._move_base = self.canvas.surface.copy()
            self._move_base.fill((0, 0, 0, 0), pygame.Rect(sx, sy, sw2, sh2))
            self.selection = (sx, sy, sw2, sh2)
            self._move_candidate = None

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
                # Start from the clean base (hole already punched once).
                # NOTE: _move_base has per-pixel alpha, so blitting it
                # straight onto `surface` alpha-COMPOSITES rather than
                # overwrites — anywhere alpha is 0 (the punched hole) the
                # destination's existing pixels show through unchanged,
                # leaving a trail of the selection at every old position it
                # passed through. Clearing to transparent first makes the
                # blit land as a real replace instead of a blend.
                surface.fill((0, 0, 0, 0))
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

    def _open_file(self):
        """Kick off a file-open dialog in the background. Does not block —
        the actual image load happens once _poll_pending_file_op() sees the
        dialog process has finished (checked once per frame from run())."""
        if self._pending_file_op is not None:
            return  # a dialog is already open, don't spawn a second one
        proc = spawn_open_dialog()
        self._pending_file_op = {"kind": "open", "proc": proc, "started": time.time()}

    def _save_file(self, save_as=False):
        path = self.current_file
        if save_as or not path:
            if self._pending_file_op is not None:
                return
            default = self.current_file or str(Path.home() / "untitled.png")
            proc = spawn_save_dialog(default)
            self._pending_file_op = {"kind": "save", "proc": proc, "started": time.time()}
            return
        self._do_save(path)

    def _do_save(self, path):
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

    def _poll_pending_file_op(self):
        """Called once per frame from run(). Checks whether a background
        open/save dialog has finished, WITHOUT ever blocking — this is what
        keeps the window responsive while zenity/kdialog/tkinter start up,
        instead of the old subprocess.run()/tkinter-mainloop call freezing
        the whole app until the dialog closed."""
        op = self._pending_file_op
        if op is None:
            return
        proc = op["proc"]
        if proc.poll() is None:
            # Still running. Give up after a very long wait so a stuck
            # dialog process can't wedge the app forever.
            if time.time() - op["started"] > 600:
                proc.kill()
                self._pending_file_op = None
            return
        out, _ = proc.communicate()
        self._pending_file_op = None
        path = (out or "").strip()
        if not path:
            return  # user cancelled
        if op["kind"] == "open":
            self.load_image(path)
        else:
            self._do_save(path)

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
            self.clock.tick(30)
            running = self.handle_events()
            self._poll_pending_file_op()
            self.render()
        pygame.quit()
        sys.exit(0)
