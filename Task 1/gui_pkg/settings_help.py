"""
settings_help.py - Help tab and settings dialog extraction.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

from api_client import ISBNLookup

from .center_window import center_toplevel


def create_help_tab(self):
    """Create help tab."""
    frame = ttk.Frame(self.notebook)
    self.notebook.add(frame, text="❓ Help")

    help_text = """
BOOKSTORE MANAGEMENT SYSTEM — User Guide

⚙️ Settings
  - Title shows the store name from Settings (saved in data/bookstore_profile.json).
  - Input bookstore name/address/contact, email, Google Books API key (used for ISBN fetch).

🛒 SALES POS
  - Products are looked up by ISBN (books) or GTIN (non-book items); they must exist in Inventory first.
  - USB barcode scanner: click the ISBN/GTIN field, scan — most guns send Enter after the code to add the line.
  - Or type the code and press Enter, or use ➕ Add to cart. Set Quantity before adding; each add uses that qty.
  - 📷 Scan: opens the webcam in continuous mode. The same code only adds again after it has been out of view
    for about 1.25 seconds (then scan again). Close the camera window or press Esc to stop.
  - Select a customer to apply loyalty discount at checkout. Checkout creates a receipt and updates stock.

📚 INVENTORY
  - Two sub-tabs: 📖 Book and non-book (GTIN) products.
  - Books: enter ISBN → Fetch Details (Google Books / Open Library fallback), edit fields, set price/stock,
    category, optional cover/reorder settings, then save to inventory.
  - Non-book: add/edit by GTIN, category, brand, image, and reorder options similar to books.
  - Lists show current stock; you can edit or remove items. Reorder fields feed the Reports “Reorder Reminder”.

👥 CUSTOMERS
  - Register and edit customers; loyalty points accrue from spend (e.g. points per HKD 10).
  - Tiers (Standard / Bronze / Silver / Gold) control discount rate at checkout.

🧑‍💼 STAFF
  - Maintain staff records (ID, role, contact). Use check-in / check-out for today’s attendance.
  - Search filters the staff list; double-click or use buttons as labeled on screen.

🏭 SUPPLIERS
  - Add suppliers and the product keys (ISBN/GTIN) they can supply, with optional unit prices for PO lines.
  - Used when building purchase orders and resolving line pricing.

📋 PURCHASE ORDERS
  - New purchase order: pick supplier, add lines (key, qty, unit price), save.
  - Search PO list; double-click a row or use View / Edit to open details and update status (Draft / Sent / Received / Cancelled).

📊 REPORTS
  - Reorder Reminder: products at or below reorder level, with related PO hint columns where applicable.
  - Summary: product count, customer count, today’s sales total (HKD).
  - Transactions: past receipts; search by text fields then Clear to reset.

💾 DATA
  - JSON files in the data/ folder (inventory, customers, sales history, suppliers, POs, staff, attendance, etc.).
  - Loaded at startup; saved after typical edits, checkout, and dialogs that persist changes.
    """

    text_widget = tk.Text(frame, wrap=tk.WORD, font=("Courier", 10))
    text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    text_widget.insert(tk.END, help_text.strip())
    text_widget.config(state=tk.DISABLED)


def show_settings(self):
    """Show settings dialog."""
    dialog = tk.Toplevel(self.root)
    dialog.title("Settings - Bookstore Profile")
    dialog.geometry("620x420")
    dialog.transient(self.root)
    dialog.grab_set()

    body = ttk.Frame(dialog, padding=12)
    body.pack(fill=tk.BOTH, expand=True)

    ttk.Label(body, text="Bookstore name:").grid(row=0, column=0, sticky="w", pady=4)
    name_entry = ttk.Entry(body, width=52)
    name_entry.grid(row=0, column=1, sticky="ew", pady=4)
    name_entry.insert(0, self.store.bookstore_name or "ABC Bookstore")

    ttk.Label(body, text="Address:").grid(row=1, column=0, sticky="nw", pady=4)
    addr_text = tk.Text(body, height=5, width=52)
    addr_text.grid(row=1, column=1, sticky="ew", pady=4)
    if self.store.bookstore_address:
        addr_text.insert("1.0", self.store.bookstore_address)

    ttk.Label(body, text="Contact person:").grid(row=2, column=0, sticky="w", pady=4)
    contact_entry = ttk.Entry(body, width=52)
    contact_entry.grid(row=2, column=1, sticky="ew", pady=4)
    contact_entry.insert(0, self.store.bookstore_contact_name or "")

    ttk.Label(body, text="Contact No.:").grid(row=3, column=0, sticky="w", pady=4)
    phone_entry = ttk.Entry(body, width=52)
    phone_entry.grid(row=3, column=1, sticky="ew", pady=4)
    phone_entry.insert(0, self.store.bookstore_phone or "")

    ttk.Label(body, text="Email:").grid(row=4, column=0, sticky="w", pady=4)
    email_entry = ttk.Entry(body, width=52)
    email_entry.grid(row=4, column=1, sticky="ew", pady=4)
    email_entry.insert(0, self.store.bookstore_email or "")

    ttk.Label(body, text="Google Books API key:").grid(row=5, column=0, sticky="w", pady=4)
    api_key_entry = ttk.Entry(body, width=52, show="*")
    api_key_entry.grid(row=5, column=1, sticky="ew", pady=4)
    api_key_entry.insert(0, self.store.google_books_api_key or "")

    tip = "These details are printed in purchase orders sent to suppliers."
    ttk.Label(body, text=tip, foreground="gray").grid(
        row=6, column=0, columnspan=2, sticky="w", pady=(8, 2)
    )

    btn_row = ttk.Frame(body)
    btn_row.grid(row=7, column=0, columnspan=2, sticky="e", pady=(10, 0))

    def save_settings():
        profile = {
            "bookstore_name": (name_entry.get() or "").strip() or "ABC Bookstore",
            "bookstore_address": addr_text.get("1.0", "end").strip(),
            "bookstore_contact_name": (contact_entry.get() or "").strip(),
            "bookstore_phone": (phone_entry.get() or "").strip(),
            "bookstore_email": (email_entry.get() or "").strip(),
            "google_books_api_key": (api_key_entry.get() or "").strip(),
        }
        self.store.apply_bookstore_profile(profile)
        ISBNLookup.set_api_key(self.store.google_books_api_key or "")
        self._refresh_bookstore_name_ui()
        ok = self.data_manager.save_bookstore_profile(self.store.bookstore_profile_dict())
        if ok:
            self.status_var.set("Bookstore profile saved")
            messagebox.showinfo("Settings", "Bookstore profile saved")
            dialog.destroy()
        else:
            messagebox.showerror("Settings", "Failed to save bookstore profile")

    ttk.Button(btn_row, text="Save", command=save_settings).pack(side=tk.LEFT, padx=5)
    ttk.Button(btn_row, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
    body.columnconfigure(1, weight=1)
    center_toplevel(dialog, self.root)
