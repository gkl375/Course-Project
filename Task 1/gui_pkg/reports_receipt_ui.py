"""
reports_receipt_ui.py - Reports refresh and receipt/store-name UI helpers.
"""

from __future__ import annotations

import tkinter as tk
import tkinter.font as tkfont
from tkinter import ttk

from .center_window import center_toplevel


def refresh_reports(self):
    """Refresh reports (reorder reminders + summary stats)."""
    created = self.store.auto_draft_reorder_purchase_orders()
    if created:
        self.data_manager.save_purchase_orders(self.store._purchase_orders)
        if hasattr(self, "purchase_orders_tree"):
            # Ensure auto-drafted POs are visible in the PO tab list.
            self._po_search_query = ""
            if hasattr(self, "po_search_entry"):
                try:
                    self.po_search_entry.delete(0, tk.END)
                except Exception:
                    pass
            self.refresh_purchase_orders_display()

    for item in self.low_stock_tree.get_children():
        self.low_stock_tree.delete(item)

    reminders = []
    for p in self.store.get_reorder_products():
        related_po = self.store.find_related_po_for_reorder_display(p.get_product_key())
        po_ts = 0.0
        if related_po is not None:
            try:
                po_ts = float(related_po.created.timestamp())
            except Exception:
                po_ts = 0.0
        reminders.append((p, related_po, po_ts))
    # Newest related PO first; no PO last; then urgency (stock vs reorder level), then name.
    reminders.sort(
        key=lambda row: (
            -row[2],
            row[0].stock - row[0].reorder_level(),
            row[0].name,
        )
    )
    for p, related_po, _ in reminders:
        self.low_stock_tree.insert(
            "",
            tk.END,
            values=(
                p.product_type_name(),
                p.get_product_key()[:50],
                p.name[:50],
                f"{p.stock}",
                f"{p.reorder_level()}",
                related_po.po_id if related_po else "",
                related_po.status if related_po else "",
            ),
        )

    if hasattr(self, "reports_products_var"):
        self.reports_products_var.set(f"Total Products: {len(self.store.get_all_products())}")
    if hasattr(self, "reports_customers_var"):
        self.reports_customers_var.set(f"Total Customers: {len(self.store._customers)}")
    if hasattr(self, "reports_sales_var"):
        self.reports_sales_var.set(f"Daily Sales: HKD {self.store.get_sales_total(1):.2f}")


def _show_receipt_dialog(self, text: str) -> None:
    """Show receipt in monospace text so columns align cleanly."""
    win = tk.Toplevel(self.root)
    win.title("Receipt")
    win.transient(self.root)

    lines = text.splitlines()
    max_line_len = max((len(s) for s in lines), default=52)
    row_count = len(lines)
    disp_w = min(max(max_line_len + 2, 52), 120)
    disp_h = min(max(row_count + 2, 14), 42)

    families = set(tkfont.families())
    mono = "Consolas" if "Consolas" in families else (
        "Courier New" if "Courier New" in families else "Courier"
    )
    mono_font = (mono, 10)

    outer = ttk.Frame(win, padding=10)
    outer.pack(fill=tk.BOTH, expand=True)
    text_frame = ttk.Frame(outer)
    text_frame.pack(fill=tk.BOTH, expand=True)
    yscroll = ttk.Scrollbar(text_frame)
    yscroll.pack(side=tk.RIGHT, fill=tk.Y)
    txt = tk.Text(
        text_frame,
        width=disp_w,
        height=disp_h,
        font=mono_font,
        wrap=tk.NONE,
        relief=tk.SOLID,
        borderwidth=1,
        padx=6,
        pady=6,
        yscrollcommand=yscroll.set,
    )
    txt.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    yscroll.config(command=txt.yview)
    txt.insert("1.0", text)
    txt.configure(state=tk.DISABLED)

    btn_row = ttk.Frame(outer)
    btn_row.pack(fill=tk.X, pady=(10, 0))
    ttk.Button(btn_row, text="OK", command=win.destroy).pack(side=tk.RIGHT)
    win.update_idletasks()
    win.minsize(360, 280)
    center_toplevel(win, self.root)


def _refresh_bookstore_name_ui(self) -> None:
    """Sync window title + toolbar title with current bookstore name."""
    name = (self.store.bookstore_name or "").strip() or "ABC Bookstore"
    self.root.title(f"{name} Management System")
    if hasattr(self, "bookstore_title_var"):
        self.bookstore_title_var.set(f"📚 {name} Management System")
