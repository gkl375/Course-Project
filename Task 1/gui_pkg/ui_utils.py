"""
ui_utils.py - Reusable GUI clipboard/tree helper utilities.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk


def copy_to_clipboard(self, text: str) -> None:
    s = str(text or "")
    if not s:
        return
    try:
        self.root.clipboard_clear()
        self.root.clipboard_append(s)
        self.root.update_idletasks()
        if hasattr(self, "status_var"):
            self.status_var.set(f"Copied: {s}")
    except Exception:
        pass


def enable_tree_id_copy(self, tree: ttk.Treeview, id_col_index: int = 0, label: str = "ID") -> None:
    """Enable Ctrl+C and right-click menu to copy an ID column from a treeview."""

    def get_selected_id() -> str:
        sel = tree.selection()
        if not sel:
            return ""
        vals = tree.item(sel[0], "values") or []
        if len(vals) <= id_col_index:
            return ""
        return str(vals[id_col_index]).strip()

    def do_copy(_evt=None):
        v = get_selected_id()
        if v:
            self._copy_to_clipboard(v)

    tree.bind("<Control-c>", do_copy)
    tree.bind("<Control-C>", do_copy)

    menu = tk.Menu(tree, tearoff=0)
    menu.add_command(label=f"Copy {label}", command=do_copy)

    def popup(event):
        try:
            row_id = tree.identify_row(event.y)
            if row_id:
                tree.selection_set(row_id)
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            try:
                menu.grab_release()
            except Exception:
                pass

    tree.bind("<Button-3>", popup)
