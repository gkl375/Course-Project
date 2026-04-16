"""
Tkinter shell for the bookstore app.

BookstorePOS (this module) owns the root window, one Store instance, a DataManager
(pointing at the data/ folder), and a SalesManager(store). Tab UIs live under
gui_pkg/ (inventory, sales, customers, staff, suppliers, POs, reports, help).

Startup: gui_pkg.app_lifecycle.load_data_async reads JSON via DataManager into Store
(inventory, customers, staff, attendance, suppliers, POs, profile, sales history).
Ongoing saves: actions call DataManager.save_* as needed; window close and explicit
save flush the same JSON files under data/.
"""

import tkinter as tk
from tkinter import ttk
from typing import Optional

from PIL import ImageTk
from models import Book, NonBook, Staff
from gui_pkg.po_glue import (
    create_purchase_orders_tab as _create_purchase_orders_tab_glue,
    refresh_purchase_orders_display as _refresh_purchase_orders_display_glue,
    new_purchase_order_dialog as _new_purchase_order_dialog_glue,
    edit_purchase_order_dialog as _edit_purchase_order_dialog_glue,
    view_purchase_order as _view_purchase_order_glue,
    delete_purchase_order as _delete_purchase_order_glue,
    create_reports_tab as _create_reports_tab_glue,
    refresh_transactions_display as _refresh_transactions_display_glue,
    search_transactions_tab as _search_transactions_tab_glue,
    clear_transactions_search as _clear_transactions_search_glue,
    view_selected_transaction as _view_selected_transaction_glue,
    search_purchase_orders_tab as _search_purchase_orders_tab_glue,
    clear_purchase_orders_search as _clear_purchase_orders_search_glue,
)
from gui_pkg.inventory_tab import (
    create_inventory_tab as _create_inventory_tab,
    refresh_inventory_display as _refresh_inventory_display_inventory,
    search_inventory as _search_inventory,
    clear_inventory_search as _clear_inventory_search,
    add_book_to_inventory as _add_book_to_inventory,
    add_nonbook_to_inventory as _add_nonbook_to_inventory,
    _on_nb_category_selected as _on_nb_category_selected_inventory,
    _on_book_category_selected as _on_book_category_selected_inventory,
    edit_inventory_item as _edit_inventory_item_inventory,
    _edit_book_dialog as _edit_book_dialog_inventory,
    _edit_nonbook_dialog as _edit_nonbook_dialog_inventory,
    delete_inventory_item as _delete_inventory_item_inventory,
    _on_inventory_mode_tab_changed as _on_inventory_mode_tab_changed_inventory,
    _on_inventory_tree_select as _on_inventory_tree_select_inventory,
    _on_inventory_select as _on_inventory_select_inventory,
    _set_cover_preview as _set_cover_preview_inventory,
    _set_nonbook_preview as _set_nonbook_preview_inventory,
    _nonbook_preview_summary_text as _nonbook_preview_summary_text_inventory,
    _load_and_show_cover_async as _load_and_show_cover_async_inventory,
    _load_and_show_nonbook_preview_async as _load_and_show_nonbook_preview_async_inventory,
    _get_cover_dir as _get_cover_dir_inventory,
    _ensure_cover_dir as _ensure_cover_dir_inventory,
    _cover_path_for_isbn as _cover_path_for_isbn_inventory,
    _save_cover_image_bytes as _save_cover_image_bytes_inventory,
    _import_cover_image_from_file as _import_cover_image_from_file_inventory,
    _nonbook_image_path_for_gtin as _nonbook_image_path_for_gtin_inventory,
    _import_nonbook_product_image_from_file as _import_nonbook_product_image_from_file_inventory,
    _open_large_cover_view as _open_large_cover_view_inventory,
    _open_large_nonbook_preview as _open_large_nonbook_preview_inventory,
)

from gui_pkg.customers_tab import (
    create_customers_tab as _create_customers_tab_customers,
    search_customers_tab as _search_customers_tab_customers,
    clear_customers_search as _clear_customers_search_customers,
    add_new_customer as _add_new_customer_customers,
    modify_customer as _modify_customer_customers,
    delete_customer as _delete_customer_customers,
    refresh_customers_display as _refresh_customers_display_customers,
)

from gui_pkg.staff_attendance_tab import (
    create_staff_tab as _create_staff_tab_staff_attendance,
    _staff_attendance_range_today as _staff_attendance_range_today_staff_attendance,
    _staff_attendance_range_clear as _staff_attendance_range_clear_staff_attendance,
    _attendance_range_from_entries as _attendance_range_from_entries_staff_attendance,
    refresh_selected_staff_attendance as _refresh_selected_staff_attendance_staff_attendance,
    _update_staff_check_toggle_button as _update_staff_check_toggle_button_staff_attendance,
    staff_check_toggle as _staff_check_toggle_staff_attendance,
    _selected_staff_id as _selected_staff_id_staff_attendance,
    _staff_editor_dialog as _staff_editor_dialog_staff_attendance,
    add_new_staff as _add_new_staff_staff_attendance,
    modify_staff as _modify_staff_staff_attendance,
    staff_check_in as _staff_check_in_staff_attendance,
    staff_check_out as _staff_check_out_staff_attendance,
    refresh_staff_display as _refresh_staff_display_staff_attendance,
    refresh_attendance_display as _refresh_attendance_display_staff_attendance,
    search_staff_tab as _search_staff_tab_staff_attendance,
    clear_staff_search as _clear_staff_search_staff_attendance,
)

from gui_pkg.suppliers_tab import (
    create_suppliers_tab as _create_suppliers_tab_suppliers,
    refresh_suppliers_display as _refresh_suppliers_display_suppliers,
    add_new_supplier as _add_new_supplier_suppliers,
    modify_supplier as _modify_supplier_suppliers,
    edit_supplier_catalog as _edit_supplier_catalog_suppliers,
    delete_supplier as _delete_supplier_suppliers,
    search_suppliers_tab as _search_suppliers_tab_suppliers,
    clear_suppliers_search as _clear_suppliers_search_suppliers,
)
from gui_pkg.sales_tab import (
    create_sales_tab as _create_sales_tab_sales,
    scan_barcode as _scan_barcode_sales,
    search_and_add as _search_and_add_sales,
    add_to_cart as _add_to_cart_sales,
    clear_cart as _clear_cart_sales,
    refresh_cart_display as _refresh_cart_display_sales,
    _refresh_customer_display as _refresh_customer_display_sales,
    search_customer as _search_customer_sales,
    _on_cart_tree_double_click as _on_cart_tree_double_click_sales,
    _on_cart_selection_changed as _on_cart_selection_changed_sales,
    _reselect_cart_row_by_key as _reselect_cart_row_by_key_sales,
    decrease_selected_cart_qty as _decrease_selected_cart_qty_sales,
    increase_selected_cart_qty as _increase_selected_cart_qty_sales,
    apply_selected_cart_qty_from_entry as _apply_selected_cart_qty_from_entry_sales,
    _cart_quantity_for_key as _cart_quantity_for_key_sales,
    show_cart_product_details as _show_cart_product_details_sales,
    delete_cart_item as _delete_cart_item_sales,
    checkout as _checkout_sales,
)
from gui_pkg.app_lifecycle import (
    load_data_async as _load_data_async_app,
    on_window_close as _on_window_close_app,
)
from gui_pkg.settings_help import (
    create_help_tab as _create_help_tab_settings_help,
    show_settings as _show_settings_settings_help,
)
from gui_pkg.reports_receipt_ui import (
    refresh_reports as _refresh_reports_reports_ui,
    _show_receipt_dialog as _show_receipt_dialog_reports_ui,
    _refresh_bookstore_name_ui as _refresh_bookstore_name_ui_reports_ui,
)
from gui_pkg.ui_utils import (
    copy_to_clipboard as _copy_to_clipboard_ui_utils,
    enable_tree_id_copy as _enable_tree_id_copy_ui_utils,
)
from gui_pkg.isbn_fetch import (
    fetch_isbn_details as _fetch_isbn_details_isbn,
    _on_isbn_fetched as _on_isbn_fetched_isbn,
)
from gui_pkg.layout_bootstrap import (
    setup_root_window as _setup_root_window_layout,
    create_widgets as _create_widgets_layout,
)
from gui_pkg.init_state import init_backend_and_state as _init_backend_and_state_init


class BookstorePOS:
    """Main GUI application."""
    
    def __init__(self, root: tk.Tk):
        """Initialize GUI."""
        self.root = root
        self._setup_root_window()
        self._init_backend_and_state()

        # Build GUI
        self.create_widgets()
        self._refresh_bookstore_name_ui()

        self.root.protocol("WM_DELETE_WINDOW", self.on_window_close)

        # Load data after UI is responsive (avoid blocking startup / input)
        self.root.after(50, self.load_data_async)
    
    def create_widgets(self):
        return _create_widgets_layout(self)

    def _setup_root_window(self) -> None:
        return _setup_root_window_layout(self)

    def _init_backend_and_state(self) -> None:
        return _init_backend_and_state_init(self)
    
    def create_sales_tab(self):
        """Create POS sales tab."""
        return _create_sales_tab_sales(self)
    
    def create_inventory_tab(self):
        """Create inventory management tab (Book and Nonbook)."""
        # Inventory UI extracted to gui_pkg/inventory_tab.py.
        return _create_inventory_tab(self)
        
    
    def create_customers_tab(self):
        """Create customer management tab."""
        return _create_customers_tab_customers(self)
        

    def create_staff_tab(self):
        """Create staff and attendance tab."""
        return _create_staff_tab_staff_attendance(self)

    def _staff_attendance_range_today(self) -> None:
        return _staff_attendance_range_today_staff_attendance(self)

    def _staff_attendance_range_clear(self) -> None:
        return _staff_attendance_range_clear_staff_attendance(self)

    def _attendance_range_from_entries(self) -> tuple[str, str]:
        return _attendance_range_from_entries_staff_attendance(self)

    def refresh_selected_staff_attendance(self) -> None:
        return _refresh_selected_staff_attendance_staff_attendance(self)

    def _update_staff_check_toggle_button(self, date_str: str = "", staff_id: str = "") -> None:
        return _update_staff_check_toggle_button_staff_attendance(
            self, date_str=date_str, staff_id=staff_id
        )

    def staff_check_toggle(self) -> None:
        return _staff_check_toggle_staff_attendance(self)

    def _selected_staff_id(self) -> Optional[str]:
        return _selected_staff_id_staff_attendance(self)

    def _staff_editor_dialog(self, title: str, staff: Optional[Staff] = None):
        return _staff_editor_dialog_staff_attendance(self, title=title, staff=staff)

    def add_new_staff(self):
        return _add_new_staff_staff_attendance(self)

    def modify_staff(self):
        return _modify_staff_staff_attendance(self)

    def staff_check_in(self):
        return _staff_check_in_staff_attendance(self)

    def staff_check_out(self):
        return _staff_check_out_staff_attendance(self)

    def refresh_staff_display(self):
        return _refresh_staff_display_staff_attendance(self)

    def refresh_attendance_display(
        self,
        staff_id: str = "",
        date_from: str = "",
        date_to: str = "",
    ) -> None:
        return _refresh_attendance_display_staff_attendance(
            self, staff_id=staff_id, date_from=date_from, date_to=date_to
            )
    
    def create_suppliers_tab(self):
        """Create supplier management tab."""
        return _create_suppliers_tab_suppliers(self)

    def create_purchase_orders_tab(self):
        return _create_purchase_orders_tab_glue(self)

    def refresh_purchase_orders_display(self) -> None:
        return _refresh_purchase_orders_display_glue(self)

    def new_purchase_order_dialog(self) -> None:
        return _new_purchase_order_dialog_glue(self)

    def edit_purchase_order_dialog(self) -> None:
        return _edit_purchase_order_dialog_glue(self)

    def view_purchase_order(self) -> None:
        return _view_purchase_order_glue(self)

    def delete_purchase_order(self) -> None:
        return _delete_purchase_order_glue(self)
    
    def refresh_suppliers_display(self):
        """Refresh suppliers table."""
        return _refresh_suppliers_display_suppliers(self)
    
    def add_new_supplier(self):
        """Add a new supplier."""
        return _add_new_supplier_suppliers(self)
    
    def modify_supplier(self):
        """Modify selected supplier basic info."""
        return _modify_supplier_suppliers(self)
        
    
    def edit_supplier_catalog(self):
        """Edit product catalog for the selected supplier (Book ISBN or Nonbook GTIN in inventory)."""
        return _edit_supplier_catalog_suppliers(self)
    
    def delete_supplier(self):
        """Delete selected supplier."""
        return _delete_supplier_suppliers(self)
    
    def create_reports_tab(self):
        return _create_reports_tab_glue(self)

    def refresh_transactions_display(self):
        return _refresh_transactions_display_glue(self)

    def search_customers_tab(self):
        return _search_customers_tab_customers(self)

    def clear_customers_search(self):
        return _clear_customers_search_customers(self)

    def search_staff_tab(self):
        return _search_staff_tab_staff_attendance(self)

    def clear_staff_search(self):
        return _clear_staff_search_staff_attendance(self)

    def search_suppliers_tab(self):
        return _search_suppliers_tab_suppliers(self)

    def clear_suppliers_search(self):
        return _clear_suppliers_search_suppliers(self)

    def search_purchase_orders_tab(self):
        return _search_purchase_orders_tab_glue(self)

    def clear_purchase_orders_search(self):
        return _clear_purchase_orders_search_glue(self)

    def search_transactions_tab(self):
        return _search_transactions_tab_glue(self)

    def clear_transactions_search(self):
        return _clear_transactions_search_glue(self)

    def view_selected_transaction(self):
        return _view_selected_transaction_glue(self)
    
    def create_help_tab(self):
        return _create_help_tab_settings_help(self)
    
    # Helper methods
    def scan_barcode(self):
        return _scan_barcode_sales(self)
    
    def search_and_add(self):
        return _search_and_add_sales(self)
    
    def add_to_cart(self):
        return _add_to_cart_sales(self)
    
    def clear_cart(self):
        return _clear_cart_sales(self)
    
    def refresh_cart_display(self):
        return _refresh_cart_display_sales(self)
    
    def _refresh_customer_display(self):
        return _refresh_customer_display_sales(self)
    
    def search_customer(self):
        return _search_customer_sales(self)
    
    def _on_cart_tree_double_click(self, event: tk.Event) -> None:
        return _on_cart_tree_double_click_sales(self, event)

    def _on_cart_selection_changed(self, _event: tk.Event | None = None) -> None:
        return _on_cart_selection_changed_sales(self, _event)

    def _reselect_cart_row_by_key(self, key: str) -> None:
        return _reselect_cart_row_by_key_sales(self, key)

    def decrease_selected_cart_qty(self) -> None:
        return _decrease_selected_cart_qty_sales(self)

    def increase_selected_cart_qty(self) -> None:
        return _increase_selected_cart_qty_sales(self)

    def apply_selected_cart_qty_from_entry(self) -> None:
        return _apply_selected_cart_qty_from_entry_sales(self)
    
    def _cart_quantity_for_key(self, key: str) -> int:
        return _cart_quantity_for_key_sales(self, key)
    
    def show_cart_product_details(self) -> None:
        return _show_cart_product_details_sales(self)
    
    def delete_cart_item(self):
        return _delete_cart_item_sales(self)
    
    def add_new_customer(self):
        """Add new customer."""
        return _add_new_customer_customers(self)
        
    
    def modify_customer(self):
        """Modify selected customer (name, telephone)."""
        return _modify_customer_customers(self)
        
    
    def delete_customer(self):
        """Delete selected customer."""
        return _delete_customer_customers(self)
        
    
    def fetch_isbn_details(self):
        return _fetch_isbn_details_isbn(self)

    def _on_isbn_fetched(self, isbn: str, data):
        return _on_isbn_fetched_isbn(self, isbn, data)
    
    def add_book_to_inventory(self):
        """Add book to inventory."""
        return _add_book_to_inventory(self)
    
    def _on_nb_category_selected(self, event=None):
        """Update subcategory combobox when Nonbook category changes."""
        return _on_nb_category_selected_inventory(self, event)

    def _on_book_category_selected(self, event=None):
        """Update subcategory combobox when Book category changes."""
        return _on_book_category_selected_inventory(self, event)
    
    def add_nonbook_to_inventory(self):
        """Add non-book product to inventory."""
        return _add_nonbook_to_inventory(self)
    
    def refresh_inventory_display(self):
        return _refresh_inventory_display_inventory(self)

    def search_inventory(self):
        return _search_inventory(self)

    def clear_inventory_search(self):
        return _clear_inventory_search(self)
    
    def edit_inventory_item(self):
        """Edit selected inventory item (Book or Nonbook)."""
        return _edit_inventory_item_inventory(self)
    
    def _edit_book_dialog(self, book: Book):
        """Open edit dialog for a Book."""
        return _edit_book_dialog_inventory(self, book)
    
    def _edit_nonbook_dialog(self, nb: NonBook):
        """Open edit dialog for a Nonbook."""
        return _edit_nonbook_dialog_inventory(self, nb)
    
    def delete_inventory_item(self):
        """Delete selected inventory item (Book or Nonbook)."""
        return _delete_inventory_item_inventory(self)

    def _on_inventory_mode_tab_changed(self, event=None) -> None:
        """Clear selection in the hidden inventory table when switching Book / Nonbook tabs."""
        return _on_inventory_mode_tab_changed_inventory(self, event)

    def _on_inventory_tree_select(self, source: ttk.Treeview) -> None:
        """Keep a single selection across Books / Nonbooks tables."""
        return _on_inventory_tree_select_inventory(self, source)

    def _on_inventory_select(self):
        """Update Book cover preview and Nonbook product preview from current tree selections."""
        return _on_inventory_select_inventory(self)

    def _set_cover_preview(self, photo: Optional[ImageTk.PhotoImage], text: str):
        return _set_cover_preview_inventory(self, photo, text)

    def _set_nonbook_preview(self, photo: Optional[ImageTk.PhotoImage], text: str):
        return _set_nonbook_preview_inventory(self, photo, text)

    def _nonbook_preview_summary_text(self, nb: NonBook) -> str:
        return _nonbook_preview_summary_text_inventory(self, nb)

    def _get_cover_dir(self) -> str:
        """Return directory path for cached cover images."""
        return _get_cover_dir_inventory(self)

    def _ensure_cover_dir(self) -> None:
        """Ensure cover cache directory exists."""
        return _ensure_cover_dir_inventory(self)

    def _cover_path_for_isbn(self, isbn: str) -> str:
        """Canonical local cover path for a given ISBN."""
        return _cover_path_for_isbn_inventory(self, isbn)

    def _save_cover_image_bytes(self, isbn: str, content: bytes) -> str:
        """Save raw image bytes as a local cover file and return its path."""
        return _save_cover_image_bytes_inventory(self, isbn, content)

    def _import_cover_image_from_file(self, isbn: str, src_path: str) -> Optional[str]:
        """Import a user-selected image file as the cover for an ISBN."""
        return _import_cover_image_from_file_inventory(self, isbn, src_path)

    def _nonbook_image_path_for_gtin(self, gtin: str) -> str:
        """Canonical local path for a Nonbook product image."""
        return _nonbook_image_path_for_gtin_inventory(self, gtin)

    def _import_nonbook_product_image_from_file(self, gtin: str, src_path: str) -> Optional[str]:
        """Import a user-selected image file as the product preview for a GTIN."""
        return _import_nonbook_product_image_from_file_inventory(self, gtin, src_path)

    def _open_large_cover_view(self):
        """Open a separate window showing a larger version of the current cover (Book only)."""
        return _open_large_cover_view_inventory(self)
        

    def _load_and_show_cover_async(self, book: Book):
        """Fetch cover image (if any) without blocking UI."""
        return _load_and_show_cover_async_inventory(self, book)
        

    def _load_and_show_nonbook_preview_async(self, nb: NonBook) -> None:
        """Load product image for Nonbook preview without blocking the UI."""
        return _load_and_show_nonbook_preview_async_inventory(self, nb)
        

    def _open_large_nonbook_preview(self) -> None:
        """Open a larger view of the Nonbook product image (if any)."""
        return _open_large_nonbook_preview_inventory(self)
        
    
    def refresh_customers_display(self):
        """Refresh customers table."""
        return _refresh_customers_display_customers(self)
        
    
    def refresh_reports(self):
        return _refresh_reports_reports_ui(self)

    def _show_receipt_dialog(self, text: str) -> None:
        return _show_receipt_dialog_reports_ui(self, text)

    def _refresh_bookstore_name_ui(self) -> None:
        return _refresh_bookstore_name_ui_reports_ui(self)

    def _copy_to_clipboard(self, text: str) -> None:
        return _copy_to_clipboard_ui_utils(self, text)

    def _enable_tree_id_copy(self, tree: ttk.Treeview, id_col_index: int = 0, label: str = "ID") -> None:
        return _enable_tree_id_copy_ui_utils(self, tree, id_col_index=id_col_index, label=label)
    
    def checkout(self):
        return _checkout_sales(self)
    
    def load_data_async(self):
        return _load_data_async_app(self)

    def on_window_close(self):
        return _on_window_close_app(self)

    def show_settings(self):
        return _show_settings_settings_help(self)


if __name__ == "__main__":
    root = tk.Tk()
    app = BookstorePOS(root)
    root.mainloop()