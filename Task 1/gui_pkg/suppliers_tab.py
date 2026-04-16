"""
suppliers_tab.py - Extracted Suppliers UI & logic from gui.py.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

import utils
from models import Book, NonBook, Supplier

from .center_window import center_toplevel


def create_suppliers_tab(self):
    """Create supplier management tab."""
    frame = ttk.Frame(self.notebook)
    self.notebook.add(frame, text="🏭 Suppliers")

    search_bar = ttk.Frame(frame)
    search_bar.pack(fill=tk.X, padx=5, pady=(5, 0))
    ttk.Label(search_bar, text="Search suppliers:").pack(side=tk.LEFT)
    self.suppliers_search_entry = ttk.Entry(search_bar, width=30)
    self.suppliers_search_entry.pack(side=tk.LEFT, padx=5)
    ttk.Button(
        search_bar, text="Search", command=self.search_suppliers_tab
    ).pack(side=tk.LEFT, padx=2)
    ttk.Button(
        search_bar, text="Clear", command=self.clear_suppliers_search
    ).pack(side=tk.LEFT, padx=2)

    tree_frame = ttk.LabelFrame(frame, text="Suppliers", padding=10)
    tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    self.suppliers_tree = ttk.Treeview(
        tree_frame,
        columns=("ID", "Name", "Address", "ContactPerson", "Phone", "Email", "Catalog"),
        height=15,
        show="headings",
    )
    self.suppliers_tree.column("ID", width=100)
    self.suppliers_tree.column("Name", width=160)
    self.suppliers_tree.column("Address", width=180)
    self.suppliers_tree.column("ContactPerson", width=130)
    self.suppliers_tree.column("Phone", width=120)
    self.suppliers_tree.column("Email", width=170)
    self.suppliers_tree.column("Catalog", width=90)

    self.suppliers_tree.heading("ID", text="Supplier ID")
    self.suppliers_tree.heading("Name", text="Name")
    self.suppliers_tree.heading("Address", text="Address")
    self.suppliers_tree.heading("ContactPerson", text="Contact person")
    self.suppliers_tree.heading("Phone", text="Phone")
    self.suppliers_tree.heading("Email", text="Email")
    self.suppliers_tree.heading("Catalog", text="Catalog items")

    self.suppliers_tree.pack(fill=tk.BOTH, expand=True)
    self.suppliers_tree.bind("<Double-1>", lambda e: self.modify_supplier())
    self._enable_tree_id_copy(
        self.suppliers_tree, id_col_index=0, label="Supplier ID"
    )

    button_frame = ttk.Frame(frame)
    button_frame.pack(fill=tk.X, padx=5, pady=5)
    ttk.Button(
        button_frame, text="➕ Add New", command=self.add_new_supplier
    ).pack(side=tk.LEFT, padx=5)
    ttk.Button(
        button_frame, text="✏️ Modify Selected", command=self.modify_supplier
    ).pack(side=tk.LEFT, padx=5)
    ttk.Button(
        button_frame,
        text="📚 Edit and View Catalog",
        command=self.edit_supplier_catalog,
    ).pack(side=tk.LEFT, padx=5)
    ttk.Button(
        button_frame, text="🗑️ Delete Selected", command=self.delete_supplier
    ).pack(side=tk.LEFT, padx=5)

    self.refresh_suppliers_display()


def refresh_suppliers_display(self):
    """Refresh suppliers table."""
    if not hasattr(self, "suppliers_tree"):
        return
    for item in self.suppliers_tree.get_children():
        self.suppliers_tree.delete(item)
    query = getattr(self, "_suppliers_search_query", "").strip().lower()
    for sup in sorted(
        self.store.get_all_suppliers(),
        key=lambda s: (s.person_id.lower(), s.name.lower()),
    ):
        if query:
            haystack = " ".join(
                [
                    sup.person_id,
                    sup.name,
                    sup.contact_person,
                    sup.phone,
                    sup.email,
                    sup.address,
                ]
            ).lower()
            if query not in haystack:
                continue
        keys = sup.catalog_keys
        n = len(keys)
        self.suppliers_tree.insert(
            "",
            tk.END,
            values=(
                sup.person_id,
                sup.name,
                sup.address or "",
                sup.contact_person or "",
                sup.phone or "",
                sup.email or "",
                str(n),
            ),
        )


def add_new_supplier(self):
    """Add a new supplier."""
    dialog = tk.Toplevel(self.root)
    dialog.title("Add Supplier")
    dialog.geometry("500x320")
    dialog.transient(self.root)

    ttk.Label(dialog, text="Name:").grid(row=0, column=0, sticky="w", padx=10, pady=5)
    name_entry = ttk.Entry(dialog, width=35)
    name_entry.grid(row=0, column=1, padx=10, pady=5)

    ttk.Label(dialog, text="Address:").grid(row=1, column=0, sticky="w", padx=10, pady=5)
    addr_entry = ttk.Entry(dialog, width=35)
    addr_entry.grid(row=1, column=1, padx=10, pady=5)

    ttk.Label(dialog, text="Contact person:").grid(row=2, column=0, sticky="w", padx=10, pady=5)
    person_entry = ttk.Entry(dialog, width=35)
    person_entry.grid(row=2, column=1, padx=10, pady=5)

    ttk.Label(dialog, text="Telephone:").grid(row=3, column=0, sticky="w", padx=10, pady=5)
    tel_entry = ttk.Entry(dialog, width=35)
    tel_entry.grid(row=3, column=1, padx=10, pady=5)

    ttk.Label(dialog, text="Email:").grid(row=4, column=0, sticky="w", padx=10, pady=5)
    email_entry = ttk.Entry(dialog, width=35)
    email_entry.grid(row=4, column=1, padx=10, pady=5)

    def save():
        name = name_entry.get().strip()
        address = addr_entry.get().strip()
        contact_person = person_entry.get().strip()
        phone = tel_entry.get().strip()
        email = email_entry.get().strip()
        if not name:
            messagebox.showerror("Error", "Name is required")
            return

        sid = None
        for _ in range(30):
            cand = utils.generate_supplier_id()
            if self.store.get_supplier(cand) is None:
                sid = cand
                break
        if sid is None:
            messagebox.showerror("Error", "Could not allocate supplier ID")
            return

        sup = Supplier(
            name,
            sid,
            contact_person=contact_person,
            address=address,
            phone=phone,
            email=email,
        )
        if self.store.add_supplier(sup):
            self.data_manager.save_suppliers(self.store._suppliers)
            messagebox.showinfo("Success", f"Supplier {sid} created")
            dialog.destroy()
            self.refresh_suppliers_display()
        else:
            messagebox.showerror("Error", "Failed to add supplier")

    ttk.Button(dialog, text="Save", command=save).grid(
        row=5, column=0, columnspan=2, sticky="ew", padx=10, pady=10
    )
    name_entry.focus()
    center_toplevel(dialog, self.root)


def modify_supplier(self):
    """Modify selected supplier basic info."""
    selection = self.suppliers_tree.selection()
    if not selection:
        messagebox.showwarning("Warning", "Please select a supplier")
        return
    sid = str(self.suppliers_tree.item(selection[0], "values")[0])
    sup = self.store.get_supplier(sid)
    if not sup:
        messagebox.showerror("Error", "Supplier not found")
        return

    dialog = tk.Toplevel(self.root)
    dialog.title("Modify Supplier")
    dialog.geometry("520x340")
    dialog.transient(self.root)

    ttk.Label(dialog, text="Supplier ID:").grid(
        row=0, column=0, sticky="w", padx=10, pady=5
    )
    ttk.Label(dialog, text=sid).grid(row=0, column=1, sticky="w", padx=10, pady=5)

    ttk.Label(dialog, text="Name:").grid(row=1, column=0, sticky="w", padx=10, pady=5)
    name_entry = ttk.Entry(dialog, width=35)
    name_entry.insert(0, sup.name)
    name_entry.grid(row=1, column=1, padx=10, pady=5)

    ttk.Label(dialog, text="Address:").grid(row=2, column=0, sticky="w", padx=10, pady=5)
    addr_entry = ttk.Entry(dialog, width=35)
    addr_entry.insert(0, sup.address or "")
    addr_entry.grid(row=2, column=1, padx=10, pady=5)

    ttk.Label(dialog, text="Contact person:").grid(
        row=3, column=0, sticky="w", padx=10, pady=5
    )
    person_entry = ttk.Entry(dialog, width=35)
    person_entry.insert(0, sup.contact_person or "")
    person_entry.grid(row=3, column=1, padx=10, pady=5)

    ttk.Label(dialog, text="Telephone:").grid(row=4, column=0, sticky="w", padx=10, pady=5)
    phone_entry = ttk.Entry(dialog, width=35)
    phone_entry.insert(0, sup.phone or "")
    phone_entry.grid(row=4, column=1, padx=10, pady=5)

    ttk.Label(dialog, text="Email:").grid(row=5, column=0, sticky="w", padx=10, pady=5)
    email_entry = ttk.Entry(dialog, width=35)
    email_entry.insert(0, sup.email or "")
    email_entry.grid(row=5, column=1, padx=10, pady=5)

    def save_changes():
        name = name_entry.get().strip()
        if not name:
            messagebox.showerror("Error", "Name is required")
            return
        sup.update_info(
            name=name,
            contact_person=person_entry.get().strip(),
            address=addr_entry.get().strip(),
            phone=phone_entry.get().strip(),
            email=email_entry.get().strip(),
        )
        self.data_manager.save_suppliers(self.store._suppliers)
        messagebox.showinfo("Success", "Supplier updated")
        dialog.destroy()
        self.refresh_suppliers_display()

    ttk.Button(dialog, text="Save", command=save_changes).grid(
        row=6, column=0, columnspan=2, sticky="ew", padx=10, pady=10
    )
    center_toplevel(dialog, self.root)


def edit_supplier_catalog(self):
    """Edit product catalog for the selected supplier."""
    selection = self.suppliers_tree.selection()
    if not selection:
        messagebox.showwarning("Warning", "Please select a supplier")
        return
    sid = str(self.suppliers_tree.item(selection[0], "values")[0])
    sup = self.store.get_supplier(sid)
    if not sup:
        messagebox.showerror("Error", "Supplier not found")
        return

    dialog = tk.Toplevel(self.root)
    dialog.title(f"Catalog — {sup.name}")
    dialog.geometry("720x400")
    dialog.transient(self.root)

    ttk.Label(
        dialog,
        text="Enter ISBN/GTIN and unit price (HKD). Unit price is required and used on purchase orders.",
        wraplength=680,
    ).grid(row=0, column=0, columnspan=2, sticky="w", padx=10, pady=5)

    list_frame = ttk.Frame(dialog)
    list_frame.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=10, pady=5)
    scroll = ttk.Scrollbar(list_frame)
    scroll.pack(side=tk.RIGHT, fill=tk.Y)

    cat_tree = ttk.Treeview(
        list_frame,
        columns=("Key", "UnitHKD", "Type", "Name"),
        height=12,
        show="headings",
        yscrollcommand=scroll.set,
    )
    scroll.config(command=cat_tree.yview)
    cat_tree.column("Key", width=130)
    cat_tree.column("UnitHKD", width=90)
    cat_tree.column("Type", width=70)
    cat_tree.column("Name", width=380)
    cat_tree.heading("Key", text="ISBN / GTIN")
    cat_tree.heading("UnitHKD", text="Unit Price")
    cat_tree.heading("Type", text="Type")
    cat_tree.heading("Name", text="Product")
    cat_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    prices = sup.catalog_prices
    for k in sorted(prices.keys(), key=lambda x: str(x).lower()):
        pr = float(prices.get(k, 0.0))
        p = self.store.get_product(k)
        if p is None:
            cat_tree.insert("", tk.END, values=(k, f"{pr:.2f}", "?", "(missing)"))
        else:
            cat_tree.insert(
                "",
                tk.END,
                values=(str(k), f"{pr:.2f}", p.product_type_name(), p.name[:70]),
            )

    dialog.rowconfigure(1, weight=1)
    dialog.columnconfigure(0, weight=1)

    entry_frame = ttk.Frame(dialog)
    entry_frame.grid(row=2, column=0, columnspan=2, sticky="ew", padx=10, pady=5)
    ttk.Label(entry_frame, text="ISBN/GTIN:").pack(side=tk.LEFT, padx=(0, 4))
    key_entry = ttk.Entry(entry_frame, width=22)
    key_entry.pack(side=tk.LEFT, padx=(0, 8))
    ttk.Label(entry_frame, text="Unit Price:").pack(side=tk.LEFT, padx=(0, 4))
    price_entry = ttk.Entry(entry_frame, width=10)
    price_entry.pack(side=tk.LEFT, padx=(0, 8))

    def add_product():
        raw = key_entry.get().strip()
        if not raw:
            return
        p = self.store.get_product(raw)
        if p is None:
            messagebox.showerror("Error", "No product with this ISBN/GTIN in inventory")
            return
        if not isinstance(p, (Book, NonBook)):
            messagebox.showerror("Error", "Invalid product type")
            return
        key = str(p.get_product_key())
        for iid in cat_tree.get_children():
            if str(cat_tree.item(iid, "values")[0]) == key:
                messagebox.showinfo("Info", "Already in catalog. Remove first to re-add.")
                return
        try:
            pe = price_entry.get().strip()
            if not pe:
                messagebox.showerror("Error", "Unit price is required")
                return
            unit = float(pe)
        except ValueError:
            messagebox.showerror("Error", "Invalid unit price")
            return
        cat_tree.insert(
            "",
            tk.END,
            values=(key, f"{unit:.2f}", p.product_type_name(), p.name[:70]),
        )
        key_entry.delete(0, tk.END)
        price_entry.delete(0, tk.END)

    def remove_selected():
        sel = cat_tree.selection()
        if sel:
            cat_tree.delete(sel[0])

    def update_selected_price():
        sel = cat_tree.selection()
        if not sel:
            messagebox.showwarning("Warning", "Select one catalog item first")
            return
        pe = price_entry.get().strip()
        if not pe:
            messagebox.showerror("Error", "Enter unit price to update")
            return
        try:
            unit = float(pe)
        except ValueError:
            messagebox.showerror("Error", "Invalid unit price")
            return
        iid = sel[0]
        vals = list(cat_tree.item(iid, "values"))
        if len(vals) < 4:
            return
        vals[1] = f"{unit:.2f}"
        cat_tree.item(iid, values=tuple(vals))
        price_entry.delete(0, tk.END)

    def on_select_row(_evt=None):
        sel = cat_tree.selection()
        if not sel:
            return
        vals = cat_tree.item(sel[0], "values")
        if len(vals) >= 2:
            price_entry.delete(0, tk.END)
            price_entry.insert(0, str(vals[1]))

    cat_tree.bind("<<TreeviewSelect>>", on_select_row)

    ttk.Button(entry_frame, text="Add", command=add_product).pack(
        side=tk.LEFT, padx=4
    )
    ttk.Button(entry_frame, text="Update selected price", command=update_selected_price).pack(
        side=tk.LEFT, padx=4
    )
    ttk.Button(entry_frame, text="Remove selected", command=remove_selected).pack(
        side=tk.LEFT, padx=4
    )

    def save_catalog():
        mapping: dict[str, float] = {}
        for iid in cat_tree.get_children():
            v = cat_tree.item(iid, "values")
            if len(v) >= 2:
                try:
                    mapping[str(v[0]).strip()] = float(v[1])
                except ValueError:
                    mapping[str(v[0]).strip()] = 0.0
        sup.set_catalog_prices(mapping)
        self.data_manager.save_suppliers(self.store._suppliers)
        messagebox.showinfo("Success", "Catalog saved")
        dialog.destroy()
        self.refresh_suppliers_display()

    btn_row = ttk.Frame(dialog)
    btn_row.grid(row=3, column=0, columnspan=2, pady=10)
    ttk.Button(btn_row, text="Save catalog", command=save_catalog).pack(
        side=tk.LEFT, padx=5
    )
    ttk.Button(btn_row, text="Cancel", command=dialog.destroy).pack(
        side=tk.LEFT, padx=5
    )
    center_toplevel(dialog, self.root)


def delete_supplier(self):
    """Delete selected supplier."""
    selection = self.suppliers_tree.selection()
    if not selection:
        messagebox.showwarning(
            "Warning", "Please select a supplier to delete"
        )
        return
    vals = self.suppliers_tree.item(selection[0], "values")
    sid = str(vals[0])
    name = str(vals[1])
    if not messagebox.askyesno(
        "Confirm Delete", f"Delete supplier '{name}' ({sid})?"
    ):
        return
    if self.store.delete_supplier(sid):
        self.data_manager.save_suppliers(self.store._suppliers)
        messagebox.showinfo("Success", "Supplier deleted")
        self.refresh_suppliers_display()
    else:
        messagebox.showerror("Error", "Failed to delete supplier")


def search_suppliers_tab(self):
    self._suppliers_search_query = self.suppliers_search_entry.get()
    self.refresh_suppliers_display()


def clear_suppliers_search(self):
    self._suppliers_search_query = ""
    if hasattr(self, "suppliers_search_entry"):
        self.suppliers_search_entry.delete(0, tk.END)
    self.refresh_suppliers_display()

