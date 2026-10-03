PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT DEFAULT ''
);

CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sku TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    category_id INTEGER NOT NULL,
    purchase_price REAL NOT NULL DEFAULT 0 CHECK (purchase_price >= 0),
    selling_price REAL NOT NULL DEFAULT 0 CHECK (selling_price >= 0),
    stock INTEGER NOT NULL DEFAULT 0 CHECK (stock >= 0),
    min_stock INTEGER NOT NULL DEFAULT 0 CHECK (min_stock >= 0),
    target_stock INTEGER NOT NULL DEFAULT 0 CHECK (target_stock >= 0),
    unit TEXT NOT NULL DEFAULT 'pcs',
    active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS stock_movements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL,
    movement_type TEXT NOT NULL CHECK (movement_type IN ('IN', 'OUT', 'ADJUSTMENT')),
    quantity INTEGER NOT NULL,
    stock_before INTEGER NOT NULL,
    stock_after INTEGER NOT NULL CHECK (stock_after >= 0),
    reference TEXT DEFAULT '',
    notes TEXT DEFAULT '',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_products_category ON products(category_id);
CREATE INDEX IF NOT EXISTS idx_movements_product_date ON stock_movements(product_id, created_at);
