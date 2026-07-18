"""
Toolbar icon drawing functions — one small function per tool glyph.
Split out so new tool icons can be added without touching app logic.
"""
import math
import pygame

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

