#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

python3 -m venv .build-venv
. .build-venv/bin/activate
python -m pip install --upgrade pip
python -m pip install pyinstaller
python -m PyInstaller --clean --noconfirm aurora.spec

echo
echo "Build Linux criado em: dist/aurora-chat"
echo "Execute com: ./dist/aurora-chat"
