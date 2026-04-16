"""
po_dialogs.py - Extracted Purchase Order dialogs from gui.py.
"""

import tkinter as tk
from tkinter import ttk, messagebox

from models import Book, NonBook, PurchaseOrder, PurchaseOrderLine

from .center_window import center_toplevel


def _line_row_total_str(qty_str: str, unit_str: str) -> str:
    try:
        return f"{int(str(qty_str).strip()) * float(str(unit_str).strip()):.2f}"
    except (ValueError, TypeError):
        return ""


def new_purchase_order_dialog(self) -> None:
    """Create a new PO: supplier + line items (ISBN/GTIN in inventory)."""
    suppliers = self.store.get_all_suppliers()
    if not suppliers:
        messagebox.showwarning("Suppliers", "Add at least one supplier first.")
        return

    dialog = tk.Toplevel(self.root)
    dialog.title("New purchase order")
    dialog.geometry("960x460")
    dialog.transient(self.root)

    ttk.Label(dialog, text="Supplier:").grid(row=0, column=0, sticky="w", padx=10, pady=6)
    sup_values = [f"{s.person_id} — {s.name}" for s in sorted(suppliers, key=lambda x: x.name.lower())]
    sup_combo = ttk.Combobox(dialog, values=sup_values, width=52, state="readonly")
    sup_combo.grid(row=0, column=1, sticky="ew", padx=10, pady=6)
    if sup_values:
        sup_combo.set(sup_values[0])

    ttk.Label(dialog, text="Notes (optional):").grid(row=1, column=0, sticky="nw", padx=10, pady=6)
    notes_txt = tk.Text(dialog, width=50, height=3, wrap=tk.WORD)
    notes_txt.grid(row=1, column=1, sticky="ew", padx=10, pady=6)

    lf = ttk.LabelFrame(dialog, text="Items", padding=6)
    lf.grid(row=2, column=0, columnspan=2, sticky="nsew", padx=10, pady=6)
    dialog.rowconfigure(2, weight=1)
    dialog.columnconfigure(1, weight=1)

    lt = ttk.Treeview(
        lf,
        columns=("Key", "Name", "Qty", "UnitHKD", "Total", "Status"),
        height=8,
        show="headings",
    )
    lt.column("Key", width=120, stretch=False)
    lt.column("Name", width=220, minwidth=120, stretch=True)
    lt.column("Qty", width=42, stretch=False)
    lt.column("UnitHKD", width=72, stretch=False)
    lt.column("Total", width=78, stretch=False)
    lt.column("Status", width=72, stretch=False)
    lt.heading("Key", text="ISBN / GTIN")
    lt.heading("Name", text="Product name")
    lt.heading("Qty", text="Qty")
    lt.heading("UnitHKD", text="Unit (HKD)")
    lt.heading("Total", text="Total (HKD)")
    lt.heading("Status", text="Status")
    lt.pack(fill=tk.BOTH, expand=True)

    rowf = ttk.Frame(lf)
    rowf.pack(fill=tk.X, pady=4)
    key_e = ttk.Entry(rowf, width=22)
    key_e.pack(side=tk.LEFT, padx=(0, 6))
    qty_e = ttk.Entry(rowf, width=6)
    qty_e.insert(0, "1")
    qty_e.pack(side=tk.LEFT, padx=(0, 6))

    def add_line() -> None:
        sel = sup_combo.get()
        if not sel or " — " not in sel:
            messagebox.showerror("Error", "Select a supplier first")
            return
        sid = sel.split(" — ", 1)[0].strip()
        sup = self.store.get_supplier(sid)
        raw = key_e.get().strip()
        if not raw:
            return
        try:
            q = int(qty_e.get().strip() or "1")
        except ValueError:
            messagebox.showerror("Error", "Invalid quantity")
            return
        if q < 1:
            messagebox.showerror("Error", "Quantity must be at least 1")
            return

        p = self.store.get_product(raw)
        if p is None or not isinstance(p, (Book, NonBook)):
            messagebox.showerror("Error", "Product not found in inventory (Book or Nonbook).")
            return

        k = str(p.get_product_key()).strip()
        if sup is None:
            messagebox.showerror("Error", "Supplier not found.")
            return
        # Supplier catalog check: only allow keys the supplier has.
        if k not in sup.catalog_prices:
            messagebox.showerror("Error", f"Supplier does not have catalog entry for: {k}")
            return

        for iid in lt.get_children():
            if str(lt.item(iid, "values")[0]) == k:
                messagebox.showinfo(
                    "Info",
                    "This product is already on the PO. Remove it first to change qty.",
                )
                return

        unit = sup.get_catalog_unit_price(k, float(p.price))
        us = f"{unit:.2f}"
        lt.insert(
            "",
            tk.END,
            values=(k, p.name, str(q), us, _line_row_total_str(str(q), us), "OK"),
        )
        key_e.delete(0, tk.END)

    def remove_line() -> None:
        sel = lt.selection()
        if sel:
            lt.delete(sel[0])

    ttk.Button(rowf, text="Add item", command=add_line).pack(side=tk.LEFT, padx=4)
    ttk.Button(rowf, text="Remove selected", command=remove_line).pack(side=tk.LEFT, padx=4)

    def create_po() -> None:
        sel = sup_combo.get()
        if not sel or " — " not in sel:
            messagebox.showerror("Error", "Select a supplier")
            return
        sid = sel.split(" — ", 1)[0].strip()
        sup = self.store.get_supplier(sid)

        lines: list[PurchaseOrderLine] = []
        missing: list[str] = []
        for iid in lt.get_children():
            v = lt.item(iid, "values")
            key = str(v[0]).strip()
            qty = int(v[2])
            unit = float(v[3])
            if sup is not None and key not in sup.catalog_prices:
                missing.append(key)
            lines.append(PurchaseOrderLine(key, qty, unit))

        if not lines:
            messagebox.showerror("Error", "Add at least one line item")
            return
        if missing:
            messagebox.showerror(
                "Error",
                "Cannot create PO: supplier is missing catalog entries for:\n"
                + "\n".join(missing[:10])
                + ("..." if len(missing) > 10 else ""),
            )
            return

        notes = notes_txt.get("1.0", tk.END).strip()
        for _ in range(40):
            po = PurchaseOrder(sid, lines=lines, notes=notes)
            if self.store.add_purchase_order(po):
                self.data_manager.save_purchase_orders(self.store._purchase_orders)
                messagebox.showinfo("Success", f"Created {po.po_id}")
                dialog.destroy()
                self.refresh_purchase_orders_display()
                if hasattr(self, "refresh_reports"):
                    self.refresh_reports()
                return
        messagebox.showerror("Error", "Could not allocate a unique PO number")

    bf = ttk.Frame(dialog)
    bf.grid(row=3, column=0, columnspan=2, pady=10)
    ttk.Button(bf, text="Create PO", command=create_po).pack(side=tk.LEFT, padx=8)
    ttk.Button(bf, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT, padx=8)
    center_toplevel(dialog, self.root)


def edit_purchase_order_dialog(self) -> None:
    """Edit a Draft PO (notes + line items)."""
    sel = self.purchase_orders_tree.selection()
    if not sel:
        messagebox.showwarning("Warning", "Select a purchase order")
        return

    poid = str(self.purchase_orders_tree.item(sel[0], "values")[0])
    po = self.store.get_purchase_order(poid)
    if not po:
        messagebox.showerror("Error", "Purchase order not found")
        return

    if po.status != "Draft":
        messagebox.showwarning("Not editable", "Only Draft purchase orders can be edited.")
        return

    suppliers = self.store.get_all_suppliers()
    if not suppliers:
        messagebox.showwarning("Suppliers", "Add at least one supplier first.")
        return

    dialog = tk.Toplevel(self.root)
    dialog.title(f"Edit Draft PO {po.po_id}")
    dialog.geometry("960x520")
    dialog.transient(self.root)

    ttk.Label(dialog, text="Supplier:").grid(row=0, column=0, sticky="w", padx=10, pady=6)
    sup_values = [f"{s.person_id} — {s.name}" for s in sorted(suppliers, key=lambda x: x.name.lower())]
    sup_combo = ttk.Combobox(dialog, values=sup_values, width=52, state="readonly")
    sup_combo.grid(row=0, column=1, sticky="ew", padx=10, pady=6)
    _cur_sid = str(po.supplier_id or "").strip()
    _set = False
    for v in sup_values:
        if v.startswith(_cur_sid + " — "):
            sup_combo.set(v)
            _set = True
            break
    if not _set and sup_values:
        sup_combo.set(sup_values[0])

    def _get_edit_supplier():
        sel = sup_combo.get()
        if not sel or " — " not in sel:
            return None
        sid = sel.split(" — ", 1)[0].strip()
        return self.store.get_supplier(sid)

    def _reprice_lines_for_selected_supplier() -> None:
        sp = _get_edit_supplier()
        if sp is None:
            return
        missing: list[str] = []
        for iid in lt.get_children():
            v = list(lt.item(iid, "values"))
            while len(v) < 6:
                v.append("")
            k = str(v[0]).strip()
            p = self.store.get_product(k)
            if k not in sp.catalog_prices:
                missing.append(k)
                v[5] = "Missing"
                v[4] = _line_row_total_str(v[2], v[3])
                lt.item(iid, values=tuple(v))
                continue
            fb = float(p.price) if p is not None else float(str(v[3]).strip() or 0)
            v[3] = f"{sp.get_catalog_unit_price(k, fb):.2f}"
            v[4] = _line_row_total_str(v[2], v[3])
            v[5] = "OK"
            lt.item(iid, values=tuple(v))
        if missing:
            messagebox.showwarning(
                "Catalog",
                "These items are not in the selected supplier's catalog (remove them or pick another supplier):\n"
                + "\n".join(missing[:8])
                + ("\n..." if len(missing) > 8 else ""),
            )

    ttk.Label(dialog, text="Notes:").grid(row=1, column=0, sticky="nw", padx=10, pady=6)
    notes_txt = tk.Text(dialog, width=50, height=3, wrap=tk.WORD)
    notes_txt.grid(row=1, column=1, sticky="ew", padx=10, pady=6)
    notes_txt.insert("1.0", po.notes or "")

    lf = ttk.LabelFrame(dialog, text="Items", padding=6)
    lf.grid(row=2, column=0, columnspan=2, sticky="nsew", padx=10, pady=6)
    dialog.rowconfigure(2, weight=1)
    dialog.columnconfigure(1, weight=1)

    lt = ttk.Treeview(
        lf,
        columns=("Key", "Name", "Qty", "UnitHKD", "Total", "Status"),
        height=10,
        show="headings",
    )
    lt.column("Key", width=120, stretch=False)
    lt.column("Name", width=220, minwidth=120, stretch=True)
    lt.column("Qty", width=42, stretch=False)
    lt.column("UnitHKD", width=72, stretch=False)
    lt.column("Total", width=78, stretch=False)
    lt.column("Status", width=72, stretch=False)
    lt.heading("Key", text="ISBN / GTIN")
    lt.heading("Name", text="Product name")
    lt.heading("Qty", text="Qty")
    lt.heading("UnitHKD", text="Unit (HKD)")
    lt.heading("Total", text="Total (HKD)")
    lt.heading("Status", text="Status")
    lt.pack(fill=tk.BOTH, expand=True)

    _prefill_sp = self.store.get_supplier(str(po.supplier_id or "").strip())
    # Prefill existing lines
    for ln in po.lines:
        p = self.store.get_product(ln.product_key)
        nm = p.name if p else ""
        us = f"{ln.unit_price:.2f}"
        qs = str(ln.quantity)
        st = (
            "OK"
            if _prefill_sp is not None and str(ln.product_key).strip() in _prefill_sp.catalog_prices
            else "Missing"
        )
        lt.insert(
            "",
            tk.END,
            values=(
                ln.product_key,
                nm,
                qs,
                us,
                _line_row_total_str(qs, us),
                st,
            ),
        )

    sup_combo.bind("<<ComboboxSelected>>", lambda _e: _reprice_lines_for_selected_supplier())

    rowf = ttk.Frame(lf)
    rowf.pack(fill=tk.X, pady=4)

    ttk.Label(rowf, text="ISBN / GTIN:").pack(side=tk.LEFT, padx=(0, 6))
    key_e = ttk.Entry(rowf, width=22)
    key_e.pack(side=tk.LEFT, padx=(0, 12))

    ttk.Label(rowf, text="Qty:").pack(side=tk.LEFT, padx=(0, 4))
    qty_e = ttk.Entry(rowf, width=6)
    qty_e.insert(0, "1")
    qty_e.pack(side=tk.LEFT, padx=(0, 6))

    # Keep the currently selected line item for "Update qty".
    selected_line_iid: dict[str, str | None] = {"iid": None}

    def _sync_selected_from_tree() -> None:
        sel = lt.selection()
        selected_line_iid["iid"] = sel[0] if sel else None

    def on_double_click(event) -> None:
        # Double-click Qty column (#3) to load it into the Qty input.
        col = lt.identify_column(event.x)
        iid = lt.identify_row(event.y)
        if not iid or col != "#3":
            return
        lt.selection_set(iid)
        _sync_selected_from_tree()
        v = lt.item(iid, "values")
        if len(v) >= 3:
            qty_e.delete(0, tk.END)
            qty_e.insert(0, str(v[2]))
            qty_e.focus_set()

    def update_qty() -> None:
        # Update Qty for the currently selected line.
        _sync_selected_from_tree()
        iid = selected_line_iid["iid"]
        if not iid:
            messagebox.showwarning("Warning", "Select a line item first.")
            return
        try:
            q = int(qty_e.get().strip() or "1")
        except ValueError:
            messagebox.showerror("Error", "Invalid quantity (integer expected)")
            return
        if q < 1:
            messagebox.showerror("Error", "Quantity must be at least 1")
            return
        v = list(lt.item(iid, "values"))
        while len(v) < 6:
            v.append("")
        if len(v) >= 3:
            v[2] = str(q)
            v[4] = _line_row_total_str(v[2], v[3])
            lt.item(iid, values=tuple(v))

    lt.bind("<<TreeviewSelect>>", lambda e: _sync_selected_from_tree())
    lt.bind("<Double-1>", on_double_click)
    qty_e.bind("<Return>", lambda e: update_qty())

    def add_line() -> None:
        raw = key_e.get().strip()
        if not raw:
            return
        try:
            q = int(qty_e.get().strip() or "1")
        except ValueError:
            messagebox.showerror("Error", "Invalid quantity")
            return
        if q < 1:
            messagebox.showerror("Error", "Quantity must be at least 1")
            return

        p = self.store.get_product(raw)
        if p is None or not isinstance(p, (Book, NonBook)):
            messagebox.showerror("Error", "Product not found in inventory (Book or Nonbook).")
            return

        k = str(p.get_product_key()).strip()
        sp = _get_edit_supplier()
        if sp is None:
            messagebox.showerror("Error", "Select a supplier.")
            return

        # Check supplier catalog before adding this item.
        if k not in sp.catalog_prices:
            messagebox.showerror("Error", f"Supplier does not have catalog entry for: {k}")
            return

        for iid in lt.get_children():
            if str(lt.item(iid, "values")[0]) == k:
                messagebox.showinfo(
                    "Info",
                    "This product is already on the PO. Remove it first to change qty.",
                )
                return

        unit = sp.get_catalog_unit_price(k, float(p.price))
        us = f"{unit:.2f}"
        qs = str(q)
        lt.insert(
            "",
            tk.END,
            values=(k, p.name, qs, us, _line_row_total_str(qs, us), "OK"),
        )
        key_e.delete(0, tk.END)

    def remove_line() -> None:
        sel_ln = lt.selection()
        if sel_ln:
            lt.delete(sel_ln[0])

    ttk.Button(rowf, text="Add item", command=add_line).pack(side=tk.LEFT, padx=4)
    ttk.Button(rowf, text="Remove selected", command=remove_line).pack(side=tk.LEFT, padx=4)
    ttk.Button(rowf, text="Update qty", command=update_qty).pack(side=tk.LEFT, padx=4)

    def save_po() -> None:
        new_notes = notes_txt.get("1.0", tk.END).strip()
        new_lines: list[PurchaseOrderLine] = []
        sel_sup = sup_combo.get()
        if not sel_sup or " — " not in sel_sup:
            messagebox.showerror("Error", "Select a supplier.")
            return
        new_sid = sel_sup.split(" — ", 1)[0].strip()
        sp = self.store.get_supplier(new_sid)
        if sp is None:
            messagebox.showerror("Error", "Supplier not found.")
            return
        missing: list[str] = []
        for iid in lt.get_children():
            v = lt.item(iid, "values")
            k = str(v[0]).strip()
            qty = int(v[2])
            if k not in sp.catalog_prices:
                missing.append(k)
                continue
            p = self.store.get_product(k)
            unit = (
                sp.get_catalog_unit_price(k, float(p.price))
                if p is not None
                else float(v[3])
            )
            new_lines.append(PurchaseOrderLine(k, qty, unit))

        if missing:
            messagebox.showerror(
                "Error",
                "Cannot save: selected supplier is missing catalog entries for:\n"
                + "\n".join(missing[:10])
                + ("..." if len(missing) > 10 else ""),
            )
            return
        if not new_lines:
            messagebox.showerror("Error", "Add at least one line item")
            return
        po.supplier_id = new_sid
        po.notes = new_notes
        po.lines = new_lines
        self.data_manager.save_purchase_orders(self.store._purchase_orders)
        self.refresh_purchase_orders_display()
        if hasattr(self, "refresh_reports"):
            self.refresh_reports()
        messagebox.showinfo("Saved", "Purchase order updated")
        dialog.destroy()

    bf = ttk.Frame(dialog)
    bf.grid(row=3, column=0, columnspan=2, pady=10)
    ttk.Button(bf, text="Save changes", command=save_po).pack(side=tk.LEFT, padx=8)
    ttk.Button(bf, text="Close", command=dialog.destroy).pack(side=tk.LEFT, padx=8)
    center_toplevel(dialog, self.root)


def view_purchase_order(self) -> None:
    """Show PO text and allow status change."""
    sel = self.purchase_orders_tree.selection()
    if not sel:
        messagebox.showwarning("Warning", "Select a purchase order")
        return
    poid = str(self.purchase_orders_tree.item(sel[0], "values")[0])
    po = self.store.get_purchase_order(poid)
    if not po:
        messagebox.showerror("Error", "Purchase order not found")
        return

    win = tk.Toplevel(self.root)
    win.title(f"Purchase order {po.po_id}")
    win.transient(self.root)
    win.geometry("720x520")

    txt = tk.Text(win, wrap=tk.WORD, font=("Consolas", 10), height=20, width=80)
    txt.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    txt.insert("1.0", po.format_document(self.store))
    txt.configure(state=tk.DISABLED)

    sf = ttk.Frame(win)
    sf.pack(fill=tk.X, padx=10, pady=(0, 8))
    ttk.Label(sf, text="Status:").pack(side=tk.LEFT, padx=(0, 8))
    status_var = tk.StringVar(value=po.status)
    cb = ttk.Combobox(
        sf,
        textvariable=status_var,
        values=list(PurchaseOrder.VALID_STATUSES),
        state="readonly",
        width=12,
    )
    cb.pack(side=tk.LEFT)

    def save_status() -> None:
        st = status_var.get()
        if st not in PurchaseOrder.VALID_STATUSES:
            return
        was_status = po.status
        po.status = st
        if st == "Received" and was_status != "Received":
            for ln in po.lines:
                p = self.store.get_product(ln.product_key)
                if p is not None:
                    p.stock = int(p.stock) + int(ln.quantity)
            self.data_manager.save_inventory(self.store._inventory)
            self.refresh_inventory_display()
        self.data_manager.save_purchase_orders(self.store._purchase_orders)
        self.refresh_purchase_orders_display()
        if hasattr(self, "refresh_reports"):
            self.refresh_reports()
        messagebox.showinfo("Saved", "Status updated")

    bf = ttk.Frame(win)
    bf.pack(fill=tk.X, pady=(0, 10))
    ttk.Button(bf, text="Save status", command=save_status).pack(side=tk.LEFT, padx=10)
    ttk.Button(bf, text="Close", command=win.destroy).pack(side=tk.LEFT, padx=10)
    center_toplevel(win, self.root)


def delete_purchase_order(self) -> None:
    sel = self.purchase_orders_tree.selection()
    if not sel:
        messagebox.showwarning("Warning", "Select a purchase order")
        return
    poid = str(self.purchase_orders_tree.item(sel[0], "values")[0])
    if not messagebox.askyesno("Confirm", f"Delete purchase order {poid}?"):
        return
    if self.store.delete_purchase_order(poid):
        self.data_manager.save_purchase_orders(self.store._purchase_orders)
        self.refresh_purchase_orders_display()
        if hasattr(self, "refresh_reports"):
            self.refresh_reports()
        messagebox.showinfo("Done", "Purchase order deleted")
    else:
        messagebox.showerror("Error", "Could not delete")

