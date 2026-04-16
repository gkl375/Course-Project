"""
reports_tab.py - Extracted Reports/Transactions UI logic from gui.py.
"""

import tkinter as tk
from tkinter import ttk, messagebox

from models import Receipt


def create_reports_tab(self) -> None:
    """Create reports tab."""
    frame = ttk.Frame(self.notebook)
    self.notebook.add(frame, text="📊 Reports")

    # Reorder reminder (all product types)
    low_stock_frame = ttk.LabelFrame(frame, text="🔔 Reorder Reminder", padding=10)
    low_stock_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    self.low_stock_tree = ttk.Treeview(
        low_stock_frame,
        columns=("Type", "Key", "Title", "Stock", "ReorderLvl", "PO", "POStatus"),
        height=10,
        show="headings",
    )
    self.low_stock_tree.column("Type", width=80)
    self.low_stock_tree.column("Key", width=120)
    self.low_stock_tree.column("Title", width=240)
    self.low_stock_tree.column("Stock", width=80)
    self.low_stock_tree.column("ReorderLvl", width=90)
    self.low_stock_tree.column("PO", width=110)
    self.low_stock_tree.column("POStatus", width=90)

    self.low_stock_tree.heading("Type", text="Type")
    self.low_stock_tree.heading("Key", text="ISBN / GTIN")
    self.low_stock_tree.heading("Title", text="Title")
    self.low_stock_tree.heading("Stock", text="Stock")
    self.low_stock_tree.heading("ReorderLvl", text="Reorder Lvl")
    self.low_stock_tree.heading("PO", text="Related PO")
    self.low_stock_tree.heading("POStatus", text="Status")

    self.low_stock_tree.pack(fill=tk.BOTH, expand=True)

    # Summary stats (use StringVar so refresh_reports can update)
    stats_frame = ttk.LabelFrame(frame, text="Summary Statistics", padding=10)
    stats_frame.pack(fill=tk.X, padx=5, pady=5)
    self.reports_products_var = tk.StringVar(value="Total Products: 0")
    self.reports_customers_var = tk.StringVar(value="Total Customers: 0")
    self.reports_sales_var = tk.StringVar(value="Daily Sales: HKD 0.00")
    ttk.Label(stats_frame, textvariable=self.reports_products_var, font=("Arial", 11)).pack(
        side=tk.LEFT, padx=20
    )
    ttk.Label(stats_frame, textvariable=self.reports_customers_var, font=("Arial", 11)).pack(
        side=tk.LEFT, padx=20
    )
    ttk.Label(stats_frame, textvariable=self.reports_sales_var, font=("Arial", 11)).pack(
        side=tk.LEFT, padx=20
    )

    # Transactions (previous sales)
    tx_frame = ttk.LabelFrame(frame, text="Transactions (previous sales)", padding=10)
    tx_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    tx_search = ttk.Frame(tx_frame)
    tx_search.pack(fill=tk.X, pady=(0, 5))
    ttk.Label(tx_search, text="Search transactions:").pack(side=tk.LEFT)
    self.tx_search_entry = ttk.Entry(tx_search, width=30)
    self.tx_search_entry.pack(side=tk.LEFT, padx=5)
    ttk.Button(tx_search, text="Search", command=self.search_transactions_tab).pack(
        side=tk.LEFT, padx=2
    )
    ttk.Button(tx_search, text="Clear", command=self.clear_transactions_search).pack(
        side=tk.LEFT, padx=2
    )

    self.transactions_tree = ttk.Treeview(
        tx_frame,
        columns=("ReceiptID", "Date", "CustomerID", "Customer", "Items", "Total"),
        height=10,
        show="headings",
    )
    self.transactions_tree.column("ReceiptID", width=110)
    self.transactions_tree.column("Date", width=160)
    self.transactions_tree.column("CustomerID", width=120)
    self.transactions_tree.column("Customer", width=200)
    self.transactions_tree.column("Items", width=60)
    self.transactions_tree.column("Total", width=110)
    self.transactions_tree.heading("ReceiptID", text="Receipt ID")
    self.transactions_tree.heading("Date", text="Date")
    self.transactions_tree.heading("CustomerID", text="Customer ID")
    self.transactions_tree.heading("Customer", text="Customer")
    self.transactions_tree.heading("Items", text="Items")
    self.transactions_tree.heading("Total", text="Total")
    self.transactions_tree.pack(fill=tk.BOTH, expand=True)
    self.transactions_tree.bind("<Double-1>", lambda e: self.view_selected_transaction())
    self._enable_tree_id_copy(self.transactions_tree, id_col_index=0, label="Receipt ID")

    tx_btn = ttk.Frame(frame)
    tx_btn.pack(fill=tk.X, padx=5, pady=(0, 5))
    ttk.Button(
        tx_btn, text="👁 View selected", command=self.view_selected_transaction
    ).pack(side=tk.LEFT, padx=5)
    ttk.Button(
        tx_btn, text="🔄 Refresh transactions", command=self.refresh_transactions_display
    ).pack(side=tk.LEFT, padx=5)

    self.refresh_reports()
    self.refresh_transactions_display()


def refresh_transactions_display(self) -> None:
    if not hasattr(self, "transactions_tree"):
        return
    for iid in self.transactions_tree.get_children():
        self.transactions_tree.delete(iid)

    rows = self.data_manager.load_sales_history()
    query = getattr(self, "_tx_search_query", "").strip().lower()

    def _sort_key(r: dict):
        return str(r.get("created", ""))

    rows_sorted = sorted(rows, key=_sort_key, reverse=True)
    for r in rows_sorted[:500]:
        rid = str(r.get("receipt_id", "")).strip()
        created = str(r.get("created", "")).replace("T", " ")
        cust = r.get("customer") or {}
        cust_id = str(cust.get("customer_id", "")).strip()
        cust_name = str(cust.get("name", "")).strip()
        items = r.get("items") or []
        try:
            n_items = len(items)
        except Exception:
            n_items = 0
        try:
            total = float(r.get("final_total", 0.0) or 0.0)
        except Exception:
            total = 0.0

        if query:
            haystack = " ".join([rid, created, cust_id, cust_name, str(n_items), f"{total:.2f}"]).lower()
            if query not in haystack:
                continue

        self.transactions_tree.insert(
            "",
            tk.END,
            values=(rid, created, cust_id, cust_name, str(n_items), f"HKD {total:.2f}"),
        )


def search_transactions_tab(self) -> None:
    self._tx_search_query = self.tx_search_entry.get()
    self.refresh_transactions_display()


def clear_transactions_search(self) -> None:
    self._tx_search_query = ""
    if hasattr(self, "tx_search_entry"):
        self.tx_search_entry.delete(0, tk.END)
    self.refresh_transactions_display()


def view_selected_transaction(self) -> None:
    if not hasattr(self, "transactions_tree"):
        return
    sel = self.transactions_tree.selection()
    if not sel:
        messagebox.showwarning("Transactions", "Please select a transaction")
        return

    rid = str(self.transactions_tree.item(sel[0], "values")[0]).strip()
    rows = self.data_manager.load_sales_history()
    hit = None
    for r in rows:
        if str(r.get("receipt_id", "")).strip() == rid:
            hit = r
            break

    if not hit:
        messagebox.showerror("Transactions", "Transaction not found in history")
        return

    # Prefer persisted receipt body (identical to checkout popup); else rebuild from snapshot + lines.
    text = str(hit.get("receipt_text", "") or "").strip()
    if not text:
        try:
            text = Receipt.from_saved_dict(hit, self.store).to_string()
        except Exception:
            text = ""
    if not text:
        created = str(hit.get("created", "")).replace("T", " ")
        cust = hit.get("customer") or {}
        cust_id = str(cust.get("customer_id", "")).strip()
        cust_name = str(cust.get("name", "")).strip()
        try:
            total = float(hit.get("final_total", 0.0) or 0.0)
        except Exception:
            total = 0.0
        text = (
            f"Receipt ID: {rid}\nDate: {created}\n"
            f"Customer ID: {cust_id}\nCustomer: {cust_name}\n"
            f"TOTAL: HKD {total:.2f}"
        )

    self._show_receipt_dialog(text)

