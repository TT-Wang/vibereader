#!/usr/bin/env bash
# Vibereader — one-liner install
# curl -sL https://raw.githubusercontent.com/TT-Wang/vibereader-menubar/main/install.sh | bash
set -e

DIR="$HOME/.vibereader-app"
BIN_DIR="$HOME/.local/bin"
BASE="https://raw.githubusercontent.com/TT-Wang/vibereader-menubar/main"

echo "🐷 Installing Vibereader..."

mkdir -p "$DIR" "$BIN_DIR"

# Download
echo "  Downloading..."
curl -sL "$BASE/fetch.py" -o "$DIR/fetch.py"
curl -sL "$BASE/vibereader_web.py" -o "$DIR/vibereader_web.py"

# Install Python deps (try multiple strategies for macOS compatibility)
echo "  Installing Python dependencies..."
if ! python3 -c "import feedparser, aiohttp" 2>/dev/null; then
  python3 -m pip install feedparser aiohttp 2>/dev/null \
    || python3 -m pip install --user feedparser aiohttp 2>/dev/null \
    || python3 -m pip install --break-system-packages feedparser aiohttp 2>/dev/null \
    || {
      echo ""
      echo "  ⚠️  Auto-install failed. Please install manually:"
      echo "     python3 -m pip install --user feedparser aiohttp"
      echo "  Then re-run this script."
      exit 1
    }
fi

# Verify
if ! python3 -c "import feedparser" 2>/dev/null; then
  echo "  ⚠️  feedparser not found. Run: python3 -m pip install --user feedparser"
  exit 1
fi
echo "  ✓ Dependencies OK"

# Create launcher (no browser — runs silently)
cat > "$BIN_DIR/vibereader" <<'LAUNCHER'
#!/usr/bin/env bash
cd "$HOME/.vibereader-app"
python3 vibereader_web.py &
PID=$!
echo "🐷 Vibereader running on http://localhost:8888 (pid $PID)"
echo "   Press Ctrl+C to stop."
trap "kill $PID 2>/dev/null" EXIT
wait $PID
LAUNCHER
chmod +x "$BIN_DIR/vibereader"

# Also create a background-only launcher for menubar use
cat > "$BIN_DIR/vibereader-bg" <<'LAUNCHER'
#!/usr/bin/env bash
cd "$HOME/.vibereader-app"
python3 vibereader_web.py >/dev/null 2>&1 &
echo $! > "$HOME/.vibereader-app/server.pid"
echo "🐷 Vibereader backend started (pid $!)"
LAUNCHER
chmod +x "$BIN_DIR/vibereader-bg"

# Ensure ~/.local/bin is in PATH
if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
  SHELL_RC=""
  if [ -f "$HOME/.zshrc" ]; then
    SHELL_RC="$HOME/.zshrc"
  elif [ -f "$HOME/.bashrc" ]; then
    SHELL_RC="$HOME/.bashrc"
  elif [ -f "$HOME/.bash_profile" ]; then
    SHELL_RC="$HOME/.bash_profile"
  fi

  if [ -n "$SHELL_RC" ]; then
    if ! grep -q '.local/bin' "$SHELL_RC" 2>/dev/null; then
      echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$SHELL_RC"
      echo "  Added ~/.local/bin to PATH in $(basename "$SHELL_RC")"
    fi
  fi
  export PATH="$BIN_DIR:$PATH"
fi

# Build Swift menubar app if on macOS with Swift available
if [[ "$(uname)" == "Darwin" ]] && command -v swift &>/dev/null; then
  echo "  Building menubar app..."
  REPO_DIR="$HOME/.vibereader-app/menubar-src"
  if [ -d "$REPO_DIR/.git" ]; then
    cd "$REPO_DIR" && git pull -q 2>/dev/null || true
  else
    git clone -q https://github.com/TT-Wang/vibereader-menubar.git "$REPO_DIR" 2>/dev/null || true
  fi
  if [ -d "$REPO_DIR" ]; then
    cd "$REPO_DIR"
    if swift build -q 2>/dev/null; then
      cp ".build/debug/VibereaderMenuBar" "$BIN_DIR/"
      echo "  ✓ Menubar app built"
    else
      echo "  ⚠️  Swift build failed — menubar app not available. Web dashboard still works."
    fi
  fi
fi

echo ""
echo "🐷 Done!"
echo ""
echo "   vibereader       — start dashboard (http://localhost:8888)"
echo "   vibereader-bg    — start backend silently (for menubar app)"
if command -v VibereaderMenuBar &>/dev/null 2>&1; then
  echo "   VibereaderMenuBar — start menubar app"
fi
echo ""
echo "   If commands not found, run: source ~/.zshrc"
