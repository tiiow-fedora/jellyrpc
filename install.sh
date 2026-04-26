#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BIN="$HOME/.local/bin"
CFG="$HOME/.config/jellyrpc"
SVC="$HOME/.config/systemd/user"

RED='\033[0;31m'; GRN='\033[0;32m'; YLW='\033[1;33m'; NC='\033[0m'
ok()   { echo -e "${GRN}✓${NC} $*"; }
warn() { echo -e "${YLW}!${NC} $*"; }
die()  { echo -e "${RED}✗${NC} $*" >&2; exit 1; }

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  JellyRPC Installer"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# pypresence is required
if ! python3 -c "import pypresence" 2>/dev/null; then
    warn "pypresence not found — installing..."
    pip install pypresence --break-system-packages || die "Could not install pypresence"
fi
ok "pypresence"

# optional deps
for cmd in playerctl xssstate xprintidle; do
    command -v "$cmd" &>/dev/null && ok "$cmd" || warn "$cmd not found (optional)"
done

mkdir -p "$BIN" "$CFG" "$SVC"

# daemon
cp "$SCRIPT_DIR/daemon/jellyrpc.py" "$BIN/jellyrpc.py"
chmod +x "$BIN/jellyrpc.py"
ok "Daemon installed → $BIN/jellyrpc.py"

# systemd
cp "$SCRIPT_DIR/service/jellyrpc.service" "$SVC/"
systemctl --user daemon-reload
systemctl --user enable --now jellyrpc.service
ok "systemd service enabled and started"

# config
if [ ! -f "$CFG/config.json" ]; then
    cp "$SCRIPT_DIR/config.example.json" "$CFG/config.json"
    warn "Fill in $CFG/config.json — set discord_app_id at minimum"
else
    ok "Config exists at $CFG/config.json"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Done!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "  Edit config:  nano $CFG/config.json"
echo "  Logs:         journalctl --user -fu jellyrpc"
