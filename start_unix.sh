#!/usr/bin/env sh
set -eu
cd "$(dirname "$0")"

PYTHON_BIN="${PYTHON_BIN:-python3}"

if [ ! -x ".venv/bin/python" ]; then
  echo "Membuat virtual environment..."
  "$PYTHON_BIN" -m venv .venv
fi

echo "Memasang dependency..."
.venv/bin/python -m pip install -r requirements.txt
echo "Membuka StockFlow di http://127.0.0.1:5000"
.venv/bin/python app.py
