"""
app_lifecycle.py - App data load/save lifecycle helpers.
"""

from __future__ import annotations

import threading
from tkinter import messagebox

from api_client import ISBNLookup


def load_data_async(self):
    """Load data in background so UI is immediately usable."""
    if hasattr(self, "status_var"):
        self.status_var.set("Loading data...")

    def worker():
        inventory = self.data_manager.load_inventory()
        customers = self.data_manager.load_customers()
        staff = self.data_manager.load_staff()
        attendance = self.data_manager.load_attendance_records()
        suppliers = self.data_manager.load_suppliers()
        pos = self.data_manager.load_purchase_orders()
        bookstore_profile = self.data_manager.load_bookstore_profile()

        def apply():
            self.store._inventory.clear()
            self.store._inventory.update(inventory)
            self.store._customers.clear()
            for cust in customers.values():
                self.store.add_customer(cust)
            self.store.set_staff(staff)
            self.store.set_attendance_records(attendance)
            self.store.set_suppliers(suppliers)
            self.store.set_purchase_orders(pos)
            self.store.apply_bookstore_profile(bookstore_profile)
            self.store.load_sales_history_from_disk(self.data_manager)
            ISBNLookup.set_api_key(self.store.google_books_api_key or "")
            self._refresh_bookstore_name_ui()

            self.refresh_inventory_display()
            self.refresh_customers_display()
            self.refresh_staff_display()
            self.refresh_suppliers_display()
            self.refresh_purchase_orders_display()
            self.refresh_reports()
            self.sales_manager.current_customer = None
            if hasattr(self, "customer_display_var"):
                self._refresh_customer_display()
            if hasattr(self, "status_var"):
                self.status_var.set(
                    f"Loaded {len(inventory)} products, {len(customers)} customers, "
                    f"{len(staff)} staff, {len(suppliers)} suppliers, {len(pos)} POs"
                )

            self._data_loaded_once = True

        self.root.after(0, apply)

    threading.Thread(target=worker, daemon=True).start()


def save_all_data_files(self) -> bool:
    """Write all editable domain data to JSON (same scope as toolbar Save)."""
    ok = True
    ok = self.data_manager.save_inventory(self.store._inventory) and ok
    ok = self.data_manager.save_customers(self.store._customers) and ok
    ok = self.data_manager.save_staff(self.store._staff) and ok
    ok = self.data_manager.save_attendance_records(self.store.get_attendance_records()) and ok
    ok = self.data_manager.save_suppliers(self.store._suppliers) and ok
    ok = self.data_manager.save_purchase_orders(self.store._purchase_orders) and ok
    ok = self.data_manager.save_bookstore_profile(self.store.bookstore_profile_dict()) and ok
    return ok


def on_window_close(self) -> None:
    """Quit: persist everything without a success dialog; block exit if save fails."""
    if not getattr(self, "_data_loaded_once", False):
        self.root.destroy()
        return
    if save_all_data_files(self):
        self.root.destroy()
        return
    messagebox.showerror(
        "Save failed",
        "Could not save data to disk. Fix the issue (e.g. disk space, permissions) and try closing again.",
    )
