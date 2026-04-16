"""
layout_bootstrap.py - Root window bootstrap and main widget layout.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk


def setup_root_window(self) -> None:
    """Initialize root title/size/maximized state."""
    self.root.title("ABC Bookstore Management System - Hong Kong")
    self.root.geometry("1200x700")
    try:
        self.root.state("zoomed")
    except Exception:
        pass


def create_widgets(self):
    """Create main GUI widgets."""
    toolbar = ttk.Frame(self.root)
    toolbar.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

    self.bookstore_title_var = tk.StringVar(value="📚 ABC Bookstore POS")
    ttk.Label(toolbar, textvariable=self.bookstore_title_var, font=("Arial", 14, "bold")).pack(
        side=tk.LEFT
    )

    self.status_var = tk.StringVar(value="Ready")
    ttk.Label(toolbar, textvariable=self.status_var, foreground="gray").pack(
        side=tk.LEFT, padx=15
    )

    ttk.Button(toolbar, text="⚙️ Settings", command=self.show_settings).pack(
        side=tk.RIGHT, padx=5
    )

    self.notebook = ttk.Notebook(self.root)
    self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    self.create_sales_tab()
    self.create_inventory_tab()
    self.create_customers_tab()
    self.create_staff_tab()
    self.create_suppliers_tab()
    self.create_purchase_orders_tab()
    self.create_reports_tab()
    self.create_help_tab()
