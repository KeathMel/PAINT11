#!/bin/bash
# Paint 11 installer — one command, working app.
#
#   curl -fsSL https://raw.githubusercontent.com/KeathMel/PAINT11/main/install.sh | bash
#
# Clones (or updates) the repo, installs dependencies, registers the icon
# and desktop entry. When it finishes, Paint 11 is in your application menu.

set -e

REPO="https://github.com/KeathMel/PAINT11.git"
DEST="${PAINT11_DIR:-$HOME/Paint11}"

say() { printf "\033[36m::\033[0m %s\n" "$1"; }
die() { printf "\033[31m!!\033[0m %s\n" "$1" >&2; exit 1; }

# ---- prerequisites -------------------------------------------------------
command -v git     >/dev/null 2>&1 || die "git is not installed."
command -v python3 >/dev/null 2>&1 || die "python3 is not installed."

# ---- get the code --------------------------------------------------------
fresh_clone() {
    rm -rf "$DEST"
    say "cloning into $DEST"
    git clone --depth 1 "$REPO" "$DEST"
}

if [ -d "$DEST/.git" ]; then
    say "updating existing install at $DEST"
    if ! git -C "$DEST" pull --ff-only 2>/tmp/paint11-git-err.log; then
        say "existing copy at $DEST looks corrupted (bad git objects) — re-cloning fresh"
        fresh_clone
    fi
    rm -f /tmp/paint11-git-err.log
else
    say "cloning into $DEST"
    git clone --depth 1 "$REPO" "$DEST"
fi

# the app can live at the repo root or in a Paint11/ subfolder
APP="$DEST"
[ -f "$APP/paint11.py" ] || APP="$DEST/Paint11"
[ -f "$APP/paint11.py" ] || die "could not find paint11.py — unexpected repo layout."

# ---- dependencies --------------------------------------------------------
say "installing python dependencies"
PIPFLAGS=""
if pip install --help 2>/dev/null | grep -q -- "--break-system-packages"; then
    PIPFLAGS="--break-system-packages"
fi
if [ -f "$APP/requirements.txt" ]; then
    pip install $PIPFLAGS -r "$APP/requirements.txt" || \
        pip install $PIPFLAGS --user -r "$APP/requirements.txt"
else
    pip install $PIPFLAGS pygame || pip install $PIPFLAGS --user pygame
fi

# tkinter powers the Open/Save file dialogs — it's a system package, not pip
python3 -c "import tkinter" 2>/dev/null || \
    say "note: tkinter not found — Open/Save dialogs need it (e.g. 'sudo apt install python3-tk')"

# ---- launcher ------------------------------------------------------------
say "installing launcher"
chmod +x "$APP/paint11.sh" 2>/dev/null || true

# ---- icon ------------------------------------------------------------
ICONDIR="$HOME/.local/share/icons/hicolor"
for sz in 16 24 32 48 64 128 256; do
    src="$APP/icons/paint11-${sz}.png"
    [ -f "$src" ] || continue
    mkdir -p "$ICONDIR/${sz}x${sz}/apps"
    cp "$src" "$ICONDIR/${sz}x${sz}/apps/paint11.png"
done
if [ -f "$APP/icons/paint11.png" ]; then
    mkdir -p "$ICONDIR/512x512/apps"
    cp "$APP/icons/paint11.png" "$ICONDIR/512x512/apps/paint11.png"
fi
command -v gtk-update-icon-cache >/dev/null 2>&1 && \
    gtk-update-icon-cache -f -t "$ICONDIR" 2>/dev/null || true

# ---- desktop entry -------------------------------------------------------
say "registering application"
APPDIR="$HOME/.local/share/applications"
mkdir -p "$APPDIR"
cat > "$APPDIR/Paint11.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=Paint 11
Comment=Windows 11-style paint clone with layers
Exec=$APP/paint11.sh
Path=$APP
Icon=paint11
Terminal=false
Categories=Graphics;2DGraphics;RasterGraphics;
MimeType=image/png;image/jpeg;image/bmp;image/gif;image/webp;image/tiff;
StartupWMClass=paint11
EOF
chmod +x "$APPDIR/Paint11.desktop"
command -v update-desktop-database >/dev/null 2>&1 && \
    update-desktop-database "$APPDIR" 2>/dev/null || true

say "done."
echo
echo "  Paint 11 installed to: $APP"
echo "  Launch it from your application menu, or run: $APP/paint11.sh"
echo
