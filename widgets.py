"""
Small self-contained UI pieces: hover tooltips, the canvas Resize dialog,
and the Color Picker dialog. None of these touch the Canvas/Layer model or
file I/O, so they're safe to edit without risking the main app logic.
"""
import pygame

from .theme import draw_rounded_rect, draw_text, draw_text_centered

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
