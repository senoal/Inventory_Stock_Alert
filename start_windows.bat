@echo off
setlocal
cd /d "%~dp0"

where python >nul 2>nul
if errorlevel 1 (
  echo Python tidak ditemukan. Instal Python 3.10 atau lebih baru dari https://python.org
  pause
  exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
  echo Membuat virtual environment...
  python -m venv .venv || goto :error
)

echo Memasang dependency...
".venv\Scripts\python.exe" -m pip install -r requirements.txt || goto :error

echo Membuka StockFlow di http://127.0.0.1:5000
".venv\Scripts\python.exe" app.py
exit /b 0

:error
echo Gagal menyiapkan aplikasi. Periksa pesan error di atas.
pause
exit /b 1
