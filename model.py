"""
Data model: Layer (one transparent sheet) and Canvas (the layer stack,
compositing, and undo/redo history).
"""
import pygame

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
        self.max_history = 20
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

