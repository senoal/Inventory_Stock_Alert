# StockFlow — Inventory & Stock Alert Dashboard

Prototipe aplikasi inventaris untuk retail dan UMKM. Dibangun dengan Flask, SQLite, Bootstrap 5, dan Chart.js.

## Fitur

- Dashboard KPI, tren mutasi, dan distribusi stok
- CRUD produk serta kategori
- Barang masuk, barang keluar, dan koreksi stok dengan audit trail
- Peringatan stok menipis/kritis dan rekomendasi restock
- Analisis slow-moving 30, 60, atau 90 hari
- Laporan inventaris dan ekspor CSV
- Data demo otomatis pada saat pertama dijalankan

## Menjalankan aplikasi

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

Buka `http://127.0.0.1:5000`.

Untuk memakai environment Python aktif yang sudah memiliki Flask, cukup jalankan `python app.py`.

## Menjalankan tes

```powershell
python -m unittest discover -s tests -v
```

Database lokal dibuat otomatis di `instance/inventory.sqlite3` dan tidak perlu dikonfigurasi terpisah.
