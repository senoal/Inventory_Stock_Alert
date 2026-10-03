from datetime import datetime, timedelta

from .db import get_db


def stock_status(stock, minimum):
    if stock <= 0:
        return "critical", "Habis"
    if stock <= max(1, minimum // 2):
        return "critical", "Kritis"
    if stock <= minimum:
        return "warning", "Menipis"
    return "safe", "Aman"


def apply_stock_movement(product_id, movement_type, quantity, reference="", notes=""):
    database = get_db()
    product = database.execute(
        "SELECT id, stock FROM products WHERE id = ? AND active = 1", (product_id,)
    ).fetchone()
    if product is None:
        raise ValueError("Produk tidak ditemukan.")

    quantity = int(quantity)
    if movement_type not in {"IN", "OUT", "ADJUSTMENT"}:
        raise ValueError("Jenis pergerakan stok tidak valid.")
    if movement_type != "ADJUSTMENT" and quantity <= 0:
        raise ValueError("Kuantitas harus lebih dari nol.")

    before = product["stock"]
    if movement_type == "IN":
        after = before + quantity
        recorded_quantity = quantity
    elif movement_type == "OUT":
        after = before - quantity
        recorded_quantity = quantity
    else:
        after = quantity
        recorded_quantity = after - before

    if after < 0:
        raise ValueError("Stok tidak mencukupi untuk transaksi ini.")

    try:
        database.execute(
            "UPDATE products SET stock = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (after, product_id),
        )
        database.execute(
            """
            INSERT INTO stock_movements
                (product_id, movement_type, quantity, stock_before, stock_after,
                 reference, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (product_id, movement_type, recorded_quantity, before, after, reference, notes),
        )
        database.commit()
    except Exception:
        database.rollback()
        raise
    return after


def slow_moving_products(days=60, max_units=5):
    cutoff = (datetime.now() - timedelta(days=days)).isoformat(timespec="seconds")
    rows = get_db().execute(
        """
        SELECT p.*, c.name AS category_name,
               COALESCE(SUM(CASE WHEN m.movement_type = 'OUT' THEN m.quantity ELSE 0 END), 0) AS sold_units,
               MAX(CASE WHEN m.movement_type = 'OUT' THEN m.created_at END) AS last_sale
        FROM products p
        JOIN categories c ON c.id = p.category_id
        LEFT JOIN stock_movements m ON m.product_id = p.id AND m.created_at >= ?
        WHERE p.active = 1
        GROUP BY p.id
        HAVING sold_units <= ?
        ORDER BY sold_units ASC, p.stock * p.purchase_price DESC
        """,
        (cutoff, max_units),
    ).fetchall()
    return rows
