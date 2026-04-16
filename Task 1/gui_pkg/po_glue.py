"""
po_glue.py - PO search helpers and small GUI glue methods.
"""

from __future__ import annotations

import tkinter as tk

from gui_pkg.po_tab import create_purchase_orders_tab as _create_purchase_orders_tab
from gui_pkg.po_tab import refresh_purchase_orders_display as _refresh_purchase_orders_display
from gui_pkg.po_dialogs import new_purchase_order_dialog as _new_purchase_order_dialog
from gui_pkg.po_dialogs import edit_purchase_order_dialog as _edit_purchase_order_dialog
from gui_pkg.po_dialogs import view_purchase_order as _view_purchase_order
from gui_pkg.po_dialogs import delete_purchase_order as _delete_purchase_order
from gui_pkg.reports_tab import create_reports_tab as _create_reports_tab
from gui_pkg.reports_tab import refresh_transactions_display as _refresh_transactions_display
from gui_pkg.reports_tab import search_transactions_tab as _search_transactions_tab
from gui_pkg.reports_tab import clear_transactions_search as _clear_transactions_search
from gui_pkg.reports_tab import view_selected_transaction as _view_selected_transaction


def create_purchase_orders_tab(self):
    return _create_purchase_orders_tab(self)


def refresh_purchase_orders_display(self) -> None:
    return _refresh_purchase_orders_display(self)


def new_purchase_order_dialog(self) -> None:
    return _new_purchase_order_dialog(self)


def edit_purchase_order_dialog(self) -> None:
    return _edit_purchase_order_dialog(self)


def view_purchase_order(self) -> None:
    return _view_purchase_order(self)


def delete_purchase_order(self) -> None:
    return _delete_purchase_order(self)


def create_reports_tab(self):
    return _create_reports_tab(self)


def refresh_transactions_display(self):
    return _refresh_transactions_display(self)


def search_transactions_tab(self):
    return _search_transactions_tab(self)


def clear_transactions_search(self):
    return _clear_transactions_search(self)


def view_selected_transaction(self):
    return _view_selected_transaction(self)


def search_purchase_orders_tab(self):
    self._po_search_query = self.po_search_entry.get()
    self.refresh_purchase_orders_display()


def clear_purchase_orders_search(self):
    self._po_search_query = ""
    if hasattr(self, "po_search_entry"):
        self.po_search_entry.delete(0, tk.END)
    self.refresh_purchase_orders_display()
