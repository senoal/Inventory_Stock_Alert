import sqlite3
from datetime import datetime, timedelta

import click
from flask import current_app, g


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(_error=None):
    connection = g.pop("db", None)
    if connection is not None:
        connection.close()


def init_db():
    database = get_db()
    with current_app.open_resource("schema.sql") as schema:
        database.executescript(schema.read().decode("utf-8"))
    database.commit()


def seed_db():
    database = get_db()
    if database.execute("SELECT COUNT(*) FROM products").fetchone()[0]:
        return

    categories = [
        ("Makanan", "Produk makanan kemasan"),
        ("Minuman", "Minuman siap konsumsi"),
        ("Rumah Tangga", "Kebutuhan rumah tangga"),
        ("Perawatan Diri", "Produk personal care"),
        ("ATK", "Alat tulis kantor"),
    ]
    database.executemany(
        "INSERT INTO categories (name, description) VALUES (?, ?)", categories
    )
    category_ids = {
        row["name"]: row["id"]
        for row in database.execute("SELECT id, name FROM categories").fetchall()
    }

    products = [
        ("MKN-001", "Beras Premium 5 kg", "Makanan", 68000, 76000, 42, 12, 40, "sak"),
        ("MKN-002", "Mi Instan Goreng", "Makanan", 2700, 3500, 8, 15, 60, "pcs"),
        ("MNM-001", "Air Mineral 600 ml", "Minuman", 2500, 4000, 3, 12, 48, "botol"),
        ("MNM-002", "Kopi Susu Botol", "Minuman", 7200, 10000, 0, 8, 32, "botol"),
        ("RT-001", "Sabun Cuci Piring", "Rumah Tangga", 8500, 12000, 25, 10, 30, "pouch"),
        ("RT-002", "Pembersih Lantai 800 ml", "Rumah Tangga", 14500, 19000, 31, 8, 24, "botol"),
        ("PD-001", "Sampo Herbal 170 ml", "Perawatan Diri", 18500, 24500, 18, 7, 21, "botol"),
        ("PD-002", "Pasta Gigi 190 g", "Perawatan Diri", 12800, 17000, 7, 7, 28, "pcs"),
        ("ATK-001", "Buku Tulis A5", "ATK", 3500, 5500, 64, 15, 50, "buku"),
        ("ATK-002", "Pulpen Gel Hitam", "ATK", 2200, 4000, 38, 10, 40, "pcs"),
        ("ATK-003", "Map Dokumen A4", "ATK", 4500, 7000, 29, 8, 25, "pcs"),
        ("MKN-003", "Biskuit Cokelat", "Makanan", 7800, 11000, 55, 12, 36, "pcs"),
    ]
    for sku, name, category, buy, sell, stock, minimum, target, unit in products:
        cursor = database.execute(
            """
            INSERT INTO products
                (sku, name, category_id, purchase_price, selling_price, stock,
                 min_stock, target_stock, unit)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (sku, name, category_ids[category], buy, sell, stock, minimum, target, unit),
        )
        product_id = cursor.lastrowid
        database.execute(
            """
            INSERT INTO stock_movements
                (product_id, movement_type, quantity, stock_before, stock_after,
                 reference, notes, created_at)
            VALUES (?, 'IN', ?, 0, ?, 'OPENING', 'Saldo awal demo', ?)
            """,
            (product_id, stock, stock, (datetime.now() - timedelta(days=100)).isoformat(timespec="seconds")),
        )

    sales = [
        ("MKN-001", 8, 4), ("MKN-002", 15, 6), ("MNM-001", 12, 3),
        ("MNM-002", 8, 2), ("RT-001", 2, 16), ("RT-002", 1, 72),
        ("PD-001", 3, 35), ("PD-002", 4, 12), ("ATK-001", 1, 80),
        ("ATK-002", 2, 45), ("MKN-003", 1, 76),
    ]
    for sku, quantity, days_ago in sales:
        product = database.execute(
            "SELECT id, stock FROM products WHERE sku = ?", (sku,)
        ).fetchone()
        database.execute(
            """
            INSERT INTO stock_movements
                (product_id, movement_type, quantity, stock_before, stock_after,
                 reference, notes, created_at)
            VALUES (?, 'OUT', ?, ?, ?, 'SALE-DEMO', 'Penjualan demo', ?)
            """,
            (
                product["id"], quantity, product["stock"] + quantity,
                product["stock"], (datetime.now() - timedelta(days=days_ago)).isoformat(timespec="seconds"),
            ),
        )
    database.commit()


@click.command("init-db")
def init_db_command():
    init_db()
    click.echo("Database berhasil diinisialisasi.")


def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
