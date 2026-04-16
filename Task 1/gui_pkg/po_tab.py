"""
po_tab.py - Extracted Purchase Orders tab logic from gui.py.
"""

import tkinter as tk
from tkinter import ttk


def create_purchase_orders_tab(self) -> None:
    """Purchase orders to suppliers."""
    frame = ttk.Frame(self.notebook)
    self.notebook.add(frame, text="📋 Purchase Orders")

    search_bar = ttk.Frame(frame)
    search_bar.pack(fill=tk.X, padx=5, pady=(5, 0))
    ttk.Label(search_bar, text="Search PO:").pack(side=tk.LEFT)
    self.po_search_entry = ttk.Entry(search_bar, width=30)
    self.po_search_entry.pack(side=tk.LEFT, padx=5)
    ttk.Button(search_bar, text="Search", command=self.search_purchase_orders_tab).pack(side=tk.LEFT, padx=2)
    ttk.Button(search_bar, text="Clear", command=self.clear_purchase_orders_search).pack(side=tk.LEFT, padx=2)

    tree_frame = ttk.LabelFrame(frame, text="Purchase orders", padding=10)
    tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    self.purchase_orders_tree = ttk.Treeview(
        tree_frame,
        columns=("PO", "Supplier", "Date", "Item", "Total", "Status"),
        height=14,
        show="headings",
    )
    self.purchase_orders_tree.column("PO", width=110)
    self.purchase_orders_tree.column("Supplier", width=180)
    self.purchase_orders_tree.column("Date", width=140)
    self.purchase_orders_tree.column("Item", width=52)
    self.purchase_orders_tree.column("Total", width=88)
    self.purchase_orders_tree.column("Status", width=88)
    self.purchase_orders_tree.heading("PO", text="PO #")
    self.purchase_orders_tree.heading("Supplier", text="Supplier")
    self.purchase_orders_tree.heading("Date", text="Created")
    self.purchase_orders_tree.heading("Item", text="Item")
    self.purchase_orders_tree.heading("Total", text="Total (HKD)")
    self.purchase_orders_tree.heading("Status", text="Status")
    self.purchase_orders_tree.pack(fill=tk.BOTH, expand=True)
    self.purchase_orders_tree.bind("<Double-1>", lambda e: self.view_purchase_order())
    self._enable_tree_id_copy(self.purchase_orders_tree, id_col_index=0, label="PO #")

    btn = ttk.Frame(frame)
    btn.pack(fill=tk.X, padx=5, pady=5)
    ttk.Button(btn, text="➕ New purchase order", command=self.new_purchase_order_dialog).pack(side=tk.LEFT, padx=5)
    ttk.Button(btn, text="👁 View / Edit status", command=self.view_purchase_order).pack(side=tk.LEFT, padx=5)
    ttk.Button(btn, text="✏️ Edit Draft PO", command=self.edit_purchase_order_dialog).pack(side=tk.LEFT, padx=5)
    ttk.Button(btn, text="🗑 Delete", command=self.delete_purchase_order).pack(side=tk.LEFT, padx=5)

    self.refresh_purchase_orders_display()


def refresh_purchase_orders_display(self) -> None:
    if not hasattr(self, "purchase_orders_tree"):
        return
    for iid in self.purchase_orders_tree.get_children():
        self.purchase_orders_tree.delete(iid)
    query = getattr(self, "_po_search_query", "").strip().lower()
    for po in self.store.get_all_purchase_orders():
        sup = self.store.get_supplier(po.supplier_id)
        sname = sup.name if sup else po.supplier_id
        if query:
            haystack = " ".join(
                [
                    po.po_id,
                    po.supplier_id,
                    sname,
                    po.status,
                    po.created.strftime("%Y-%m-%d %H:%M"),
                ]
            ).lower()
            if query not in haystack:
                continue
        po_total = sum(float(ln.quantity) * float(ln.unit_price) for ln in po.lines)
        self.purchase_orders_tree.insert(
            "",
            tk.END,
            values=(
                po.po_id,
                sname,
                po.created.strftime("%Y-%m-%d %H:%M"),
                str(len(po.lines)),
                f"{po_total:.2f}",
                po.status,
            ),
        )

