# StockFlow — Inventory & Stock Alert Dashboard

StockFlow adalah aplikasi inventaris portabel untuk retail dan UMKM. Aplikasi dibangun dengan Flask dan SQLite serta menyertakan seluruh aset frontend secara lokal, sehingga antarmuka dan grafik tetap berfungsi tanpa koneksi CDN.

## Fitur utama

- Dashboard KPI, grafik tren mutasi, dan distribusi stok
- Manajemen produk dan kategori
- Barang masuk, barang keluar, dan koreksi stok dengan audit trail
- Peringatan stok menipis/kritis dan rekomendasi restock
- Analisis slow-moving untuk periode 30, 60, atau 90 hari
- Laporan inventaris dan ekspor CSV
- Database demo siap pakai di `instance/inventory.sqlite3`
- Bootstrap, Bootstrap Icons, dan Chart.js tersedia secara lokal

## Persyaratan

- Python 3.10 atau lebih baru
- `pip` dan dukungan pembuatan virtual environment (`venv`)
- Koneksi internet hanya diperlukan satu kali untuk memasang Flask

## Cara termudah di Windows

1. Clone atau unduh repository ini.
2. Pastikan Python telah terpasang dan opsi **Add Python to PATH** dipilih saat instalasi.
3. Klik dua kali `start_windows.bat`.
4. Buka `http://127.0.0.1:5000` jika browser tidak terbuka otomatis.

Script tersebut membuat virtual environment dan memasang dependency secara otomatis.

## Menjalankan manual di Windows

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python app.py
```

Jika PowerShell melarang aktivasi script, virtual environment tetap dapat digunakan tanpa aktivasi:

```powershell
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe app.py
```

## Menjalankan di macOS atau Linux

```bash
chmod +x start_unix.sh
./start_unix.sh
```

Atau secara manual:

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
python app.py
```

## Konfigurasi opsional

Aplikasi berjalan pada `127.0.0.1:5000`. Nilainya dapat diubah melalui environment variable:

```powershell
$env:HOST = "0.0.0.0"
$env:PORT = "8080"
python app.py
```

Jangan gunakan `FLASK_DEBUG=1` pada komputer produksi.

## Database

Repository menyertakan database demo `instance/inventory.sqlite3`, sehingga hasil clone langsung memiliki produk dan transaksi contoh. Aplikasi tetap dapat membuat database beserta data demo secara otomatis jika file tersebut dihapus.

File sementara SQLite (`-journal`, `-shm`, dan `-wal`) tidak disimpan karena hanya berlaku untuk sesi database yang sedang berjalan.

## Menjalankan pengujian

```powershell
python -m unittest discover -s tests -v
```

Pengujian memeriksa semua halaman utama, aset frontend lokal, ekspor laporan, pencatatan mutasi, dan perlindungan terhadap stok negatif.

## Struktur penting

```text
inventory/
├── static/             CSS, JavaScript, dan library frontend lokal
├── templates/          Template halaman Jinja
├── db.py               Koneksi, inisialisasi, dan data demo
├── routes.py           Routing aplikasi
├── schema.sql          Skema database
└── services.py         Aturan bisnis inventaris
instance/
└── inventory.sqlite3   Database demo siap pakai
tests/                  Automated tests
app.py                  Entry point aplikasi
requirements.txt        Dependency Python
```

## Catatan Git

Folder `__pycache__`, file `.pyc`, `.venv`, dan file sementara SQLite sengaja tidak ikut Git. File tersebut dihasilkan khusus untuk sistem operasi atau sesi lokal dan memasukkannya justru dapat menyebabkan konflik di komputer lain. Semua source code, aset frontend, skema, dan database demo yang diperlukan aplikasi ikut repository.
