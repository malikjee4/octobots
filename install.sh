#!/usr/bin/env bash
# Install (or update) octobots into the current project directory.
#
# Usage (run from your project root):
#   curl -fsSL https://raw.githubusercontent.com/arozumenko/octobots/main/install.sh | bash
#
# What this does:
#   - Downloads a tarball from GitHub (no git clone, no nested repo)
#   - Extracts to /tmp, copies framework files to ./octobots/
#   - Installs Python dependencies
#   - Initializes .octobots/ runtime directory and seeds .claude/
#
# Safe to re-run — updates the framework without touching .octobots/ (your runtime).

set -euo pipefail

REPO="arozumenko/octobots"
BRANCH="main"
TARBALL_URL="https://github.com/$REPO/archive/refs/heads/$BRANCH.tar.gz"
TMP_DIR=$(mktemp -d)
DEST="octobots"

cleanup() { rm -rf "$TMP_DIR"; }
trap cleanup EXIT

echo "Installing octobots in $(pwd)"
echo ""

# ── Download & extract ────────────────────────────────────────────────────────

echo "Downloading..."
curl -fsSL "$TARBALL_URL" -o "$TMP_DIR/octobots.tar.gz"
tar -xzf "$TMP_DIR/octobots.tar.gz" -C "$TMP_DIR"
SRC="$TMP_DIR/octobots-$BRANCH"

# ── Copy framework files ──────────────────────────────────────────────────────
# Replaces octobots/ framework files but never touches .octobots/ (your runtime).

echo "Copying to ./$DEST/..."
rm -rf "./$DEST"
cp -r "$SRC" "./$DEST"
echo "  Done"

# ── Python dependencies ───────────────────────────────────────────────────────

echo ""
echo "Installing Python dependencies..."
if command -v pip3 &>/dev/null; then
    pip3 install -q -r "$DEST/scripts/requirements.txt"
elif command -v pip &>/dev/null; then
    pip install -q -r "$DEST/scripts/requirements.txt"
else
    echo "  ⚠  pip not found — run manually: pip install -r octobots/scripts/requirements.txt"
fi
echo "  Done"

# ── Initialize runtime ────────────────────────────────────────────────────────

echo ""
bash "$DEST/scripts/init-project.sh"

# ── .gitignore ────────────────────────────────────────────────────────────────

GITIGNORE=".gitignore"
for entry in "octobots/" ".octobots/" ".mcp.json" ".cursor/mcp.json" ".windsurf/mcp.json" ".vscode/mcp.json"; do
    grep -qF "$entry" "$GITIGNORE" 2>/dev/null || echo "$entry" >> "$GITIGNORE"
done
echo "  .gitignore updated"

# ── Done ─────────────────────────────────────────────────────────────────────

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  octobots installed"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Next steps:"
echo ""
echo "  1. Configure Telegram (optional):"
echo "     echo 'OCTOBOTS_TG_TOKEN=your-bot-token' >> .env.octobots"
echo "     echo 'OCTOBOTS_TG_OWNER=your-telegram-user-id' >> .env.octobots"
echo ""
echo "  2. Explore the project:"
echo "     octobots/start.sh scout"
echo ""
echo "  3. Start the team:"
echo "     python3 octobots/scripts/supervisor.py"
echo ""
echo "  Re-run this script at any time to update octobots."
echo ""
