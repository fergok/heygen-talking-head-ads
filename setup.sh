#!/bin/bash
# One-time setup on a Mac. Run from inside this folder:  bash setup.sh
# Puts everything where the skills expect it:
#   ~/Video Editing Test          (skills, styles, tools, review app)
#   ~/Documents/LuxeLight Claude  (brand files, hook library, winning ads)
set -e
HERE="$(cd "$(dirname "$0")" && pwd)"
VET="$HOME/Video Editing Test"
LUX="$HOME/Documents/LuxeLight Claude"

echo "1/5 Copying the editing folder to $VET"
mkdir -p "$VET"
rsync -a --ignore-existing "$HERE/Video Editing Test/" "$VET/"

echo "2/5 Copying the brand folder to $LUX"
mkdir -p "$LUX"
rsync -a --ignore-existing "$HERE/LuxeLight Claude/" "$LUX/"

echo "3/5 Linking brand files into Brands/LuxeLight"
B="$VET/Brands/LuxeLight"; mkdir -p "$B"
ln -sf "$LUX/CLAUDE.md"          "$B/brand-notes.md"
ln -sf "$LUX/product-summary.md" "$B/product-summary.md"
ln -sf "$LUX/footage.md"         "$B/footage.md"
ln -sf "$LUX/clip-picks.md"      "$B/clip-picks.md"

echo "4/5 Pointing Claude's settings at this Mac's home folder"
S="$VET/.claude/settings.json"
sed -i '' "s#/Users/jackferguson#$HOME#g" "$S"

echo "5/5 Installing Python tools (ffmpeg, whisper, torch) - takes a few minutes"
cd "$VET/tools"
[ -d venv ] || python3 -m venv venv
./venv/bin/pip install -q --upgrade pip
./venv/bin/pip install -q -r "$HERE/requirements.txt"
FF=$(./venv/bin/python -c "import imageio_ffmpeg;print(imageio_ffmpeg.get_ffmpeg_exe())")
ln -sf "$FF" venv/bin/ffmpeg
command -v ffprobe >/dev/null || echo "NOTE: install ffprobe too (brew install ffmpeg), the QA and review tools use it."
mkdir -p "$VET/tools/huggingface"

echo
echo "Done. Open Claude Code in '$HOME/Documents/LuxeLight Claude' and ask for a HeyGen ad."
echo "Review app: python3 \"$VET/.claude/skills/apply-notes/scripts/review_server.py\"  ->  http://localhost:8765"
