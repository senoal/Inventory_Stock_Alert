import csv
import io
import math
from datetime import datetime, timedelta

from flask import (
    Blueprint, Response, current_app, flash, redirect, render_template, request, url_for
)
from sqlite3 import IntegrityError

from .db import get_db
from .services import apply_stock_movement, slow_moving_products, stock_status


bp = Blueprint("main", __name__)


@bp.app_template_filter("currency")
def currency(value):
    return "Rp {:,.0f}".format(value or 0).replace(",", ".")


@bp.app_template_filter("date_id")
def date_id(value):
    if not value:
        return "—"
    try:
        return datetime.fromisoformat(value).strftime("%d %b %Y, %H:%M")
    except (TypeError, ValueError):
        return value


@bp.app_context_processor
def template_helpers():
    return {"stock_status": stock_status}


@bp.route("/")
def dashboard():
    database = get_db()
    summary = database.execute(
        """
        SELECT COUNT(*) AS products,
               COALESCE(SUM(stock), 0) AS stock_units,
               COALESCE(SUM(stock * purchase_price), 0) AS inventory_value,
               SUM(CASE WHEN stock <= min_stock THEN 1 ELSE 0 END) AS low_stock
        FROM products WHERE active = 1
        """
    ).fetchone()
    category_count = database.execute("SELECT COUNT(*) FROM categories").fetchone()[0]
    categories = database.execute(
        """
        SELECT c.name, COALESCE(SUM(p.stock), 0) AS stock
        FROM categories c LEFT JOIN products p ON p.category_id = c.id AND p.active = 1
        GROUP BY c.id ORDER BY stock DESC
        """
    ).fetchall()
    alerts = database.execute(
        """
        SELECT p.*, c.name AS category_name FROM products p
        JOIN categories c ON c.id = p.category_id
        WHERE p.active = 1 AND p.stock <= p.min_stock
        ORDER BY CASE WHEN p.stock = 0 THEN 0 ELSE 1 END, p.stock ASC LIMIT 6
        """
    ).fetchall()
    recent = database.execute(
        """
        SELECT m.*, p.name AS product_name, p.sku FROM stock_movements m
        JOIN products p ON p.id = m.product_id
        ORDER BY m.created_at DESC, m.id DESC LIMIT 7
        """
    ).fetchall()
    start = (datetime.now() - timedelta(days=29)).date().isoformat()
    trend = database.execute(
        """
        SELECT date(created_at) AS day,
               SUM(CASE WHEN movement_type = 'IN' THEN quantity ELSE 0 END) AS incoming,
               SUM(CASE WHEN movement_type = 'OUT' THEN quantity ELSE 0 END) AS outgoing
        FROM stock_movements WHERE date(created_at) >= ?
        GROUP BY date(created_at) ORDER BY day
        """,
        (start,),
    ).fetchall()
    return render_template(
        "dashboard.html", summary=summary, category_count=category_count,
        categories=categories, alerts=alerts, recent=recent, trend=trend,
        slow_count=len(slow_moving_products()),
    )


@bp.route("/products")
def products():
    database = get_db()
    query = request.args.get("q", "").strip()
    category = request.args.get("category", type=int)
    sort = request.args.get("sort", "name")
    page = max(1, request.args.get("page", 1, type=int))
    per_page = current_app.config["ITEMS_PER_PAGE"]
    order_map = {
        "name": "p.name ASC", "stock_low": "p.stock ASC", "stock_high": "p.stock DESC",
        "value": "(p.stock * p.purchase_price) DESC", "newest": "p.id DESC",
    }
    conditions = ["p.active = 1"]
    params = []
    if query:
        conditions.append("(p.name LIKE ? OR p.sku LIKE ?)")
        params.extend([f"%{query}%", f"%{query}%"])
    if category:
        conditions.append("p.category_id = ?")
        params.append(category)
    where = " AND ".join(conditions)
    total = database.execute(f"SELECT COUNT(*) FROM products p WHERE {where}", params).fetchone()[0]
    rows = database.execute(
        f"""
        SELECT p.*, c.name AS category_name FROM products p
        JOIN categories c ON c.id = p.category_id WHERE {where}
        ORDER BY {order_map.get(sort, order_map['name'])} LIMIT ? OFFSET ?
        """,
        [*params, per_page, (page - 1) * per_page],
    ).fetchall()
    categories = database.execute("SELECT * FROM categories ORDER BY name").fetchall()
    return render_template(
        "products.html", products=rows, categories=categories, page=page,
        pages=max(1, math.ceil(total / per_page)), total=total,
    )


def _product_form_data():
    return (
        request.form["sku"].strip().upper(), request.form["name"].strip(),
        request.form.get("category_id", type=int), request.form.get("purchase_price", type=float),
        request.form.get("selling_price", type=float), request.form.get("stock", type=int),
        request.form.get("min_stock", type=int), request.form.get("target_stock", type=int),
        request.form.get("unit", "pcs").strip(),
    )


@bp.route("/products/new", methods=("GET", "POST"))
def product_new():
    database = get_db()
    if request.method == "POST":
        try:
            sku, name, category_id, buy, sell, stock, minimum, target, unit = _product_form_data()
            if not sku or not name or category_id is None or min(buy, sell, stock, minimum, target) < 0:
                raise ValueError("Lengkapi data produk dengan nilai yang valid.")
            cursor = database.execute(
                """
                INSERT INTO products (sku, name, category_id, purchase_price, selling_price,
                    stock, min_stock, target_stock, unit) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (sku, name, category_id, buy, sell, stock, minimum, target, unit),
            )
            if stock:
                database.execute(
                    """INSERT INTO stock_movements (product_id, movement_type, quantity,
                    stock_before, stock_after, reference, notes)
                    VALUES (?, 'IN', ?, 0, ?, 'OPENING', 'Stok awal produk')""",
                    (cursor.lastrowid, stock, stock),
                )
            database.commit()
            flash("Produk berhasil ditambahkan.", "success")
            return redirect(url_for("main.products"))
        except (ValueError, TypeError, IntegrityError) as error:
            database.rollback()
            message = "SKU sudah digunakan." if isinstance(error, IntegrityError) else str(error)
            flash(message, "danger")
    categories = database.execute("SELECT * FROM categories ORDER BY name").fetchall()
    return render_template("product_form.html", product=None, categories=categories)


@bp.route("/products/<int:product_id>/edit", methods=("GET", "POST"))
def product_edit(product_id):
    database = get_db()
    product = database.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
    if product is None:
        flash("Produk tidak ditemukan.", "danger")
        return redirect(url_for("main.products"))
    if request.method == "POST":
        try:
            sku, name, category_id, buy, sell, _stock, minimum, target, unit = _product_form_data()
            if not sku or not name or category_id is None or min(buy, sell, minimum, target) < 0:
                raise ValueError("Lengkapi data produk dengan nilai yang valid.")
            database.execute(
                """
                UPDATE products SET sku=?, name=?, category_id=?, purchase_price=?,
                    selling_price=?, min_stock=?, target_stock=?, unit=?, updated_at=CURRENT_TIMESTAMP
                WHERE id=?
                """,
                (sku, name, category_id, buy, sell, minimum, target, unit, product_id),
            )
            database.commit()
            flash("Produk berhasil diperbarui.", "success")
            return redirect(url_for("main.products"))
        except (ValueError, TypeError, IntegrityError) as error:
            database.rollback()
            message = "SKU sudah digunakan." if isinstance(error, IntegrityError) else str(error)
            flash(message, "danger")
    categories = database.execute("SELECT * FROM categories ORDER BY name").fetchall()
    return render_template("product_form.html", product=product, categories=categories)


@bp.post("/products/<int:product_id>/delete")
def product_delete(product_id):
    database = get_db()
    database.execute("UPDATE products SET active = 0, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (product_id,))
    database.commit()
    flash("Produk dinonaktifkan. Riwayat stok tetap tersimpan.", "success")
    return redirect(url_for("main.products"))


@bp.route("/inventory", methods=("GET", "POST"))
def inventory():
    database = get_db()
    if request.method == "POST":
        try:
            product_id = request.form.get("product_id", type=int)
            movement_type = request.form["movement_type"]
            quantity = request.form.get("quantity", type=int)
            if product_id is None or quantity is None:
                raise ValueError("Produk dan kuantitas wajib diisi.")
            apply_stock_movement(
                product_id, movement_type, quantity,
                request.form.get("reference", "").strip(), request.form.get("notes", "").strip(),
            )
            flash("Pergerakan stok berhasil dicatat.", "success")
            return redirect(url_for("main.inventory"))
        except ValueError as error:
            flash(str(error), "danger")
    products = database.execute(
        "SELECT id, sku, name, stock, unit FROM products WHERE active = 1 ORDER BY name"
    ).fetchall()
    movements = database.execute(
        """
        SELECT m.*, p.name AS product_name, p.sku, p.unit FROM stock_movements m
        JOIN products p ON p.id = m.product_id ORDER BY m.created_at DESC, m.id DESC LIMIT 20
        """
    ).fetchall()
    return render_template("inventory.html", products=products, movements=movements)


@bp.route("/alerts")
def alerts():
    rows = get_db().execute(
        """
        SELECT p.*, c.name AS category_name, MAX(p.target_stock - p.stock, 0) AS reorder_qty
        FROM products p JOIN categories c ON c.id = p.category_id
        WHERE p.active = 1 AND p.stock <= p.min_stock
        ORDER BY CASE WHEN p.stock = 0 THEN 0 WHEN p.stock <= MAX(1, p.min_stock / 2) THEN 1 ELSE 2 END,
                 p.stock ASC
        """
    ).fetchall()
    return render_template("alerts.html", products=rows)


@bp.route("/slow-moving")
def slow_moving():
    days = request.args.get("days", current_app.config["SLOW_MOVING_DAYS"], type=int)
    if days not in {30, 60, 90}:
        days = 60
    max_units = request.args.get("max_units", current_app.config["SLOW_MOVING_MAX_UNITS"], type=int)
    max_units = max(0, min(max_units, 1000))
    rows = slow_moving_products(days, max_units)
    return render_template("slow_moving.html", products=rows, days=days, max_units=max_units)


@bp.route("/transactions")
def transactions():
    database = get_db()
    movement_type = request.args.get("type", "")
    date_from = request.args.get("date_from", "")
    date_to = request.args.get("date_to", "")
    conditions, params = ["1=1"], []
    if movement_type in {"IN", "OUT", "ADJUSTMENT"}:
        conditions.append("m.movement_type = ?")
        params.append(movement_type)
    if date_from:
        conditions.append("date(m.created_at) >= ?")
        params.append(date_from)
    if date_to:
        conditions.append("date(m.created_at) <= ?")
        params.append(date_to)
    rows = database.execute(
        f"""
        SELECT m.*, p.name AS product_name, p.sku, p.unit FROM stock_movements m
        JOIN products p ON p.id = m.product_id WHERE {' AND '.join(conditions)}
        ORDER BY m.created_at DESC, m.id DESC LIMIT 250
        """,
        params,
    ).fetchall()
    return render_template("transactions.html", movements=rows)


def _report_rows():
    category = request.args.get("category", type=int)
    status = request.args.get("status", "")
    conditions, params = ["p.active = 1"], []
    if category:
        conditions.append("p.category_id = ?")
        params.append(category)
    if status == "low":
        conditions.append("p.stock <= p.min_stock")
    elif status == "safe":
        conditions.append("p.stock > p.min_stock")
    return get_db().execute(
        f"""
        SELECT p.*, c.name AS category_name, p.stock * p.purchase_price AS inventory_value
        FROM products p JOIN categories c ON c.id = p.category_id
        WHERE {' AND '.join(conditions)} ORDER BY c.name, p.name
        """,
        params,
    ).fetchall()


@bp.route("/reports")
def reports():
    database = get_db()
    rows = _report_rows()
    categories = database.execute("SELECT * FROM categories ORDER BY name").fetchall()
    total_value = sum(row["inventory_value"] for row in rows)
    return render_template("reports.html", products=rows, categories=categories, total_value=total_value)


@bp.route("/reports/export.csv")
def export_report():
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["SKU", "Produk", "Kategori", "Stok", "Unit", "Minimum", "Harga Beli", "Nilai Persediaan", "Status"])
    for row in _report_rows():
        _tone, label = stock_status(row["stock"], row["min_stock"])
        writer.writerow([
            row["sku"], row["name"], row["category_name"], row["stock"], row["unit"],
            row["min_stock"], row["purchase_price"], row["inventory_value"], label,
        ])
    return Response(
        "\ufeff" + output.getvalue(), mimetype="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=inventory-report.csv"},
    )


@bp.route("/settings", methods=("GET", "POST"))
def settings():
    database = get_db()
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        if not name:
            flash("Nama kategori wajib diisi.", "danger")
        else:
            try:
                database.execute("INSERT INTO categories (name) VALUES (?)", (name,))
                database.commit()
                flash("Kategori berhasil ditambahkan.", "success")
                return redirect(url_for("main.settings"))
            except IntegrityError:
                database.rollback()
                flash("Kategori tersebut sudah ada.", "danger")
    categories = database.execute(
        """
        SELECT c.*, COUNT(p.id) AS product_count FROM categories c
        LEFT JOIN products p ON p.category_id = c.id AND p.active = 1
        GROUP BY c.id ORDER BY c.name
        """
    ).fetchall()
    return render_template("settings.html", categories=categories)
