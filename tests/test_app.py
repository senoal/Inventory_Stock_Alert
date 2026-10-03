import os
import tempfile
import unittest

from inventory import create_app
from inventory.db import get_db
from inventory.services import apply_stock_movement


class InventoryAppTest(unittest.TestCase):
    def setUp(self):
        handle, path = tempfile.mkstemp()
        os.close(handle)
        self.database_path = path
        self.app = create_app({"TESTING": True, "DATABASE": path, "SECRET_KEY": "test"})
        self.client = self.app.test_client()

    def tearDown(self):
        os.unlink(self.database_path)

    def test_main_pages_load(self):
        for path in ["/", "/products", "/inventory", "/alerts", "/slow-moving", "/transactions", "/reports", "/settings"]:
            response = self.client.get(path)
            self.assertEqual(response.status_code, 200, path)

    def test_local_frontend_assets_load(self):
        assets = [
            "/static/vendor/bootstrap/bootstrap.min.css",
            "/static/vendor/bootstrap/bootstrap.bundle.min.js",
            "/static/vendor/bootstrap-icons/bootstrap-icons.min.css",
            "/static/vendor/bootstrap-icons/fonts/bootstrap-icons.woff2",
            "/static/vendor/chartjs/chart.umd.min.js",
            "/static/css/app.css",
            "/static/js/app.js",
        ]
        for path in assets:
            response = self.client.get(path)
            try:
                self.assertEqual(response.status_code, 200, path)
                self.assertGreater(len(response.data), 100, path)
            finally:
                response.close()

    def test_report_export_is_downloadable(self):
        response = self.client.get("/reports/export.csv")
        self.assertEqual(response.status_code, 200)
        self.assertIn("text/csv", response.content_type)
        self.assertIn("inventory-report.csv", response.headers["Content-Disposition"])
        self.assertIn("SKU", response.get_data(as_text=True))

    def test_stock_movement_is_recorded(self):
        with self.app.app_context():
            product = get_db().execute("SELECT id, stock FROM products WHERE active=1 LIMIT 1").fetchone()
            after = apply_stock_movement(product["id"], "IN", 5, "TEST", "Automated test")
            self.assertEqual(after, product["stock"] + 5)
            movement = get_db().execute("SELECT * FROM stock_movements WHERE reference='TEST'").fetchone()
            self.assertIsNotNone(movement)

    def test_stock_cannot_be_negative(self):
        with self.app.app_context():
            product = get_db().execute("SELECT id, stock FROM products WHERE active=1 LIMIT 1").fetchone()
            with self.assertRaises(ValueError):
                apply_stock_movement(product["id"], "OUT", product["stock"] + 1)


if __name__ == "__main__":
    unittest.main()
