"""
init_state.py - Backend and runtime state initialization for BookstorePOS.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Optional

from PIL import ImageTk

from data_manager import DataManager
from inventory import InventoryManager
from models import Store
from sales import SalesManager


def init_backend_and_state(self) -> None:
    """Initialize backend services and runtime/widget state fields."""
    self.store = Store()
    self.data_manager = DataManager()
    self.sales_manager = SalesManager(self.store)
    self.inventory_manager = InventoryManager(self.store)

    # Declare widget attributes (assigned in create_widgets / tab methods)
    self.notebook: ttk.Notebook
    self.isbn_entry: ttk.Entry
    self.qty_entry: ttk.Entry
    self.cart_tree: ttk.Treeview
    self.customer_display_var: tk.StringVar
    self.subtotal_label: ttk.Label
    self.loyalty_tier_label: ttk.Label
    self.discount_label: ttk.Label
    self.total_label: ttk.Label
    self.add_isbn_entry: ttk.Entry
    self.fetch_btn: ttk.Button
    self.fetch_status_var: tk.StringVar
    self.add_title_entry: ttk.Entry
    self.add_subtitle_entry: ttk.Entry
    self.add_author_entry: ttk.Entry
    self.add_publisher_entry: ttk.Entry
    self.add_pub_date_entry: ttk.Entry
    self.add_subject_entry: ttk.Combobox
    self.add_book_subcategory_combo: ttk.Combobox
    self.add_nb_name_entry: ttk.Entry
    self.add_nb_brand_entry: ttk.Entry
    self.add_nb_model_entry: ttk.Entry
    self.add_nb_gtin_entry: ttk.Entry
    self.add_nb_category_combo: ttk.Combobox
    self.add_nb_subcategory_combo: ttk.Combobox
    self.add_price_entry: ttk.Entry
    self.add_stock_entry: ttk.Entry
    self.inventory_book_tree: ttk.Treeview
    self.inventory_nonbook_tree: ttk.Treeview
    self.customers_tree: ttk.Treeview
    self.staff_tree: ttk.Treeview
    self.attendance_tree: ttk.Treeview
    self.suppliers_tree: ttk.Treeview
    self.purchase_orders_tree: ttk.Treeview
    self.low_stock_tree: ttk.Treeview
    self.inventory_cover_label: tk.Label
    self.inventory_nb_preview_label: tk.Label
    self.status_var: tk.StringVar
    self.bookstore_title_var: tk.StringVar

    self._inventory_cover_photo: Optional[ImageTk.PhotoImage] = None
    self._cover_image_cache: dict[str, ImageTk.PhotoImage] = {}
    self._inventory_cover_req_id: int = 0
    self._last_fetched_isbn: str = ""
    self._last_fetched_cover_url: str = ""
    self._current_cover_isbn: Optional[str] = None
    self._large_cover_photo: Optional[ImageTk.PhotoImage] = None
    self._inventory_nb_preview_photo: Optional[ImageTk.PhotoImage] = None
    self._inventory_nb_req_id: int = 0
    self._current_nonbook_gtin: Optional[str] = None
    self._large_nb_photo: Optional[ImageTk.PhotoImage] = None
    self._inventory_search_query: str = ""
    self._inventory_search_product_type: Optional[str] = None
    # Set True after first successful apply() from load_data_async.
    self._data_loaded_once: bool = False
