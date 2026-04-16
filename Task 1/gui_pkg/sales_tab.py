"""
sales_tab.py - Extracted Sales/POS UI and logic from gui.py.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

from models import Book, NonBook
from scanner import BarcodeScanner, refocus_barcode_scanner_window

from .center_window import center_toplevel


def _pos_add_from_barcode_entry(
    self,
    *,
    require_non_empty_key: bool = True,
    refocus_cv_scanner: bool = False,
) -> bool:
    """Add ISBN/GTIN from entry + qty to cart; on success clear entry and refocus for next scan."""
    key = self.isbn_entry.get().strip()
    if not key:
        if require_non_empty_key:
            messagebox.showerror("Error", "Enter ISBN or GTIN")
        return False
    try:
        qty = int(self.qty_entry.get().strip() or "1")
    except ValueError:
        messagebox.showerror("Error", "Invalid quantity")
        if refocus_cv_scanner:
            refocus_barcode_scanner_window()
        return False
    if qty < 1:
        messagebox.showerror("Error", "Quantity must be at least 1")
        if refocus_cv_scanner:
            refocus_barcode_scanner_window()
        return False
    product = self.store.get_product(key)
    if not product:
        messagebox.showerror("Not Found", f"ISBN/GTIN {key} not in inventory")
        self.isbn_entry.selection_range(0, tk.END)
        if refocus_cv_scanner:
            refocus_barcode_scanner_window()
        else:
            self.isbn_entry.focus_set()
        return False
    if not self.sales_manager.add_to_cart(key, qty):
        messagebox.showerror(
            "Error",
            "Could not add to cart (insufficient stock or product unavailable).",
        )
        self.isbn_entry.selection_range(0, tk.END)
        if refocus_cv_scanner:
            refocus_barcode_scanner_window()
        else:
            self.isbn_entry.focus_set()
        return False
    self.isbn_entry.delete(0, tk.END)
    self.qty_entry.delete(0, tk.END)
    self.qty_entry.insert(0, "1")
    self.refresh_cart_display()
    self._reselect_cart_row_by_key(str(product.get_product_key()))
    if refocus_cv_scanner:
        refocus_barcode_scanner_window()
    else:
        self.isbn_entry.focus_set()
    return True


def create_sales_tab(self):
    """Create POS sales tab."""
    frame = ttk.Frame(self.notebook)
    self.notebook.add(frame, text="🛒 Sales POS")

    sales_main = ttk.Frame(frame)
    sales_main.pack(fill=tk.BOTH, expand=True)

    # Left: Shopping Cart
    cart_frame = ttk.LabelFrame(sales_main, text="Shopping Cart", padding=10)
    cart_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

    self.cart_tree = ttk.Treeview(
        cart_frame,
        columns=("Key", "Title", "Qty", "Price", "Total"),
        height=10,
        show="headings",
    )
    self.cart_tree.column("Key", width=130, minwidth=90)
    self.cart_tree.column("Title", width=200)
    self.cart_tree.column("Qty", width=50)
    self.cart_tree.column("Price", width=80)
    self.cart_tree.column("Total", width=80)
    self.cart_tree.heading("Key", text="ISBN / GTIN")
    self.cart_tree.heading("Title", text="Title")
    self.cart_tree.heading("Qty", text="Qty")
    self.cart_tree.heading("Price", text="Unit Price")
    self.cart_tree.heading("Total", text="Subtotal")
    self.cart_tree.pack(fill=tk.BOTH, expand=True)
    self.cart_tree.bind("<<TreeviewSelect>>", self._on_cart_selection_changed)

    right_col = ttk.Frame(sales_main)
    right_col.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=(0, 5), pady=5)
    left_frame = ttk.LabelFrame(right_col, text="Add Items to Cart", padding=10)
    left_frame.pack(side=tk.TOP, fill=tk.X)

    ttk.Label(left_frame, text="ISBN / GTIN (USB scan sends Enter):").grid(row=0, column=0, sticky="w")
    self.isbn_entry = ttk.Entry(left_frame, width=16)
    self.isbn_entry.grid(row=0, column=1, sticky="ew", padx=5)

    def _on_isbn_return(_event: tk.Event | None = None) -> str:
        _pos_add_from_barcode_entry(self, require_non_empty_key=False)
        return "break"

    self.isbn_entry.bind("<Return>", _on_isbn_return)
    ttk.Button(left_frame, text="📷 Scan", command=self.scan_barcode).grid(row=0, column=2, padx=5)
    ttk.Label(left_frame, text="Quantity:").grid(row=1, column=0, sticky="w")
    self.qty_entry = ttk.Entry(left_frame, width=8)
    self.qty_entry.insert(0, "1")
    self.qty_entry.grid(row=1, column=1, sticky="ew", padx=5)
    ttk.Button(left_frame, text="➕ Add to Cart", command=self.add_to_cart).grid(
        row=1, column=2, columnspan=2, sticky="ew"
    )

    cart_controls = ttk.LabelFrame(right_col, text="Cart Controls", padding=10)
    cart_controls.pack(side=tk.TOP, fill=tk.X, pady=(8, 0))
    qty_row = ttk.Frame(cart_controls)
    qty_row.pack(fill=tk.X)
    ttk.Label(qty_row, text="Selected qty:").pack(side=tk.LEFT)
    ttk.Button(qty_row, text="➖", width=3, command=self.decrease_selected_cart_qty).pack(
        side=tk.LEFT, padx=(6, 2)
    )
    self.cart_line_qty_entry = ttk.Entry(qty_row, width=8)
    self.cart_line_qty_entry.pack(side=tk.LEFT, padx=2)
    ttk.Button(qty_row, text="➕", width=3, command=self.increase_selected_cart_qty).pack(
        side=tk.LEFT, padx=2
    )
    ttk.Button(qty_row, text="Apply", command=self.apply_selected_cart_qty_from_entry).pack(
        side=tk.LEFT, padx=(8, 0)
    )

    action_row = ttk.Frame(cart_controls)
    action_row.pack(fill=tk.X, pady=(10, 0))
    ttk.Button(action_row, text="📋 Item details", command=self.show_cart_product_details).pack(
        side=tk.LEFT, padx=(0, 6)
    )
    ttk.Button(action_row, text="🗑️ Delete Selected", command=self.delete_cart_item).pack(
        side=tk.LEFT
    )

    checkout_frame = ttk.LabelFrame(right_col, text="Checkout", padding=10)
    checkout_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, pady=(8, 0))
    ttk.Label(checkout_frame, text="Customer:").grid(row=0, column=0, sticky="nw")
    ttk.Button(checkout_frame, text="🔍 Search", command=self.search_customer).grid(
        row=0, column=1, sticky="nw", padx=5
    )
    self.customer_display_var = tk.StringVar(value="No customer selected")
    self.customer_display_label = ttk.Label(
        checkout_frame,
        textvariable=self.customer_display_var,
        font=("Arial", 10),
        wraplength=320,
    )
    self.customer_display_label.grid(
        row=1, column=0, columnspan=3, sticky="ew", padx=(0, 5), pady=(2, 6)
    )
    ttk.Label(checkout_frame, text="Subtotal:").grid(row=2, column=0, sticky="w")
    self.subtotal_label = ttk.Label(checkout_frame, text="HKD 0.00", font=("Arial", 12, "bold"))
    self.subtotal_label.grid(row=2, column=1, columnspan=2, sticky="w")
    ttk.Label(checkout_frame, text="Loyalty:").grid(row=3, column=0, sticky="w")
    self.loyalty_tier_label = ttk.Label(
        checkout_frame, text="—", font=("Arial", 10), wraplength=320
    )
    self.loyalty_tier_label.grid(row=3, column=1, columnspan=2, sticky="ew")
    ttk.Label(checkout_frame, text="Discount:").grid(row=4, column=0, sticky="w")
    self.discount_label = ttk.Label(checkout_frame, text="HKD 0.00")
    self.discount_label.grid(row=4, column=1, columnspan=2, sticky="w")
    ttk.Label(checkout_frame, text="TOTAL:").grid(row=5, column=0, sticky="w")
    self.total_label = ttk.Label(checkout_frame, text="HKD 0.00", font=("Arial", 14, "bold"))
    self.total_label.grid(row=5, column=1, columnspan=2, sticky="w")

    checkout_btn_frame = ttk.Frame(checkout_frame)
    checkout_btn_frame.grid(row=6, column=0, columnspan=3, sticky="ew", pady=(14, 0))
    ttk.Button(checkout_btn_frame, text="✓ Checkout", command=self.checkout).pack(
        side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 4)
    )
    ttk.Button(checkout_btn_frame, text="🔄 Clear", command=self.clear_cart).pack(
        side=tk.LEFT, fill=tk.X, expand=True, padx=(4, 0)
    )

    def _sales_checkout_wrap(_evt: tk.Event) -> None:
        wf = checkout_frame.winfo_width()
        if wf < 100:
            return
        wrap = max(180, wf - 48)
        self.customer_display_label.configure(wraplength=wrap)
        self.loyalty_tier_label.configure(wraplength=wrap)

    checkout_frame.bind("<Configure>", _sales_checkout_wrap, add="+")
    left_frame.columnconfigure(1, weight=1)
    checkout_frame.columnconfigure(1, weight=1)
    checkout_frame.columnconfigure(2, weight=1)


def scan_barcode(self):
    """Webcam: keep scanning; same ISBN adds again only after it leaves the camera view. q / ESC = close."""
    added_ok = {"n": 0}

    def on_found(isbn: str) -> None:
        self.isbn_entry.delete(0, tk.END)
        self.isbn_entry.insert(0, isbn)
        if _pos_add_from_barcode_entry(
            self, require_non_empty_key=False, refocus_cv_scanner=True
        ):
            added_ok["n"] += 1
        try:
            self.root.update_idletasks()
        except tk.TclError:
            pass

    self.root.config(cursor="watch")
    try:
        self.root.update_idletasks()
        self.root.update()
        cam_ok = BarcodeScanner.scan_webcam_continuous(on_found, timeout_ms=0)
    finally:
        self.root.config(cursor="")

    if not cam_ok:
        messagebox.showerror("Scanner", "Cannot open webcam.")
    elif added_ok["n"] == 0:
        messagebox.showwarning(
            "Scanner",
            "No item was added (closed camera, timeout, or no valid ISBN).",
        )


def search_and_add(self):
    """Search for product by ISBN or GTIN and add to cart."""
    key = self.isbn_entry.get().strip()
    if not key:
        messagebox.showerror("Error", "Enter ISBN or GTIN")
        return
    product = self.store.get_product(key)
    if product:
        self.add_to_cart()
    else:
        messagebox.showerror("Not Found", f"ISBN/GTIN {key} not in inventory")


def add_to_cart(self):
    """Add item to cart by ISBN or GTIN (button)."""
    _pos_add_from_barcode_entry(self, require_non_empty_key=True)


def clear_cart(self):
    """Clear shopping cart."""
    self.sales_manager.cancel_order()
    self.refresh_cart_display()


def refresh_cart_display(self):
    """Refresh cart display."""
    for item in self.cart_tree.get_children():
        self.cart_tree.delete(item)
    if not self.sales_manager.current_order:
        self.subtotal_label.config(text="HKD 0.00")
        self.discount_label.config(text="HKD 0.00")
        self.total_label.config(text="HKD 0.00")
        if hasattr(self, "loyalty_tier_label"):
            self.loyalty_tier_label.config(text="—")
        self._refresh_customer_display()
        return
    subtotal = 0.0
    for item in self.sales_manager.current_order.get_items():
        key = item.product.get_product_key()
        subtotal += item.get_subtotal()
        self.cart_tree.insert(
            "",
            tk.END,
            values=(
                key,
                item.product.name[:40],
                item.quantity,
                f"HKD {item.product.price:.2f}",
                f"HKD {item.get_subtotal():.2f}",
            ),
        )
    self.subtotal_label.config(text=f"HKD {subtotal:.2f}")
    discount = 0.0
    if self.sales_manager.current_customer:
        rate = self.sales_manager.current_customer.get_discount_rate()
        discount = subtotal * rate
    self.discount_label.config(text=f"HKD {discount:.2f}")
    self.total_label.config(text=f"HKD {subtotal - discount:.2f}")
    self._refresh_customer_display()


def _refresh_customer_display(self):
    """Update customer display label from current selected customer."""
    if hasattr(self, "customer_display_var"):
        c = self.sales_manager.current_customer
        if c:
            self.customer_display_var.set(f"{c.person_id} - {c.name}")
        else:
            self.customer_display_var.set("No customer selected")
    if hasattr(self, "loyalty_tier_label"):
        c = self.sales_manager.current_customer
        if c:
            rate = c.get_discount_rate()
            self.loyalty_tier_label.config(text=f"{c.get_tier()}  ·  {rate * 100:.1f}% off")
        else:
            self.loyalty_tier_label.config(text="—")


def search_customer(self):
    """Search customer by ID or telephone number."""
    dialog = tk.Toplevel(self.root)
    dialog.title("Search Customer")
    dialog.geometry("520x230")
    dialog.transient(self.root)
    dialog.columnconfigure(0, weight=0)
    dialog.columnconfigure(1, weight=1)
    dialog.columnconfigure(2, weight=0)
    ttk.Label(dialog, text="Search by:", font=("Arial", 10, "bold")).grid(
        row=0, column=0, columnspan=3, sticky="w", padx=10, pady=10
    )
    search_var = tk.StringVar(value="id")
    ttk.Radiobutton(dialog, text="Customer ID", variable=search_var, value="id").grid(
        row=1, column=0, sticky="w", padx=20, pady=5
    )
    ttk.Radiobutton(dialog, text="Telephone", variable=search_var, value="phone").grid(
        row=1, column=1, sticky="w", padx=20, pady=5
    )
    ttk.Label(dialog, text="Enter value:").grid(row=2, column=0, sticky="w", padx=10, pady=5)
    search_entry = ttk.Entry(dialog, width=35)
    search_entry.grid(row=2, column=1, sticky="ew", padx=10, pady=5)
    search_entry.focus()
    result_label = ttk.Label(dialog, text="", foreground="blue")
    result_label.grid(row=3, column=0, columnspan=2, sticky="w", padx=10, pady=10)

    def perform_search():
        search_value = search_entry.get().strip()
        if not search_value:
            messagebox.showwarning("Warning", "Please enter a search value")
            return
        search_type = search_var.get()
        found_customer = None
        for customer in self.store._customers.values():
            if search_type == "id" and customer.person_id.lower() == search_value.lower():
                found_customer = customer
                break
            if search_type == "phone" and customer.telephone.lower() == search_value.lower():
                found_customer = customer
                break
        if found_customer:
            self.sales_manager.select_customer(found_customer.person_id)
            self.refresh_cart_display()
            dialog.destroy()
        else:
            result_label.config(text="✗ Customer not found", foreground="red")

    ttk.Button(dialog, text="🔍 Search", command=perform_search).grid(
        row=2, column=2, sticky="e", padx=(0, 10), pady=5
    )
    center_toplevel(dialog, self.root)


def _on_cart_tree_double_click(self, event: tk.Event) -> None:
    row_id = self.cart_tree.identify_row(event.y)
    if not row_id:
        return
    self.cart_tree.selection_set(row_id)
    self._on_cart_selection_changed(None)
    self.show_cart_product_details()


def _on_cart_selection_changed(self, _event: tk.Event | None = None) -> None:
    selection = self.cart_tree.selection()
    if not selection:
        if hasattr(self, "cart_line_qty_entry"):
            self.cart_line_qty_entry.delete(0, tk.END)
        return
    values = self.cart_tree.item(selection[0], "values")
    if len(values) < 3:
        if hasattr(self, "cart_line_qty_entry"):
            self.cart_line_qty_entry.delete(0, tk.END)
        return
    if hasattr(self, "cart_line_qty_entry"):
        self.cart_line_qty_entry.delete(0, tk.END)
        self.cart_line_qty_entry.insert(0, str(values[2]))


def _reselect_cart_row_by_key(self, key: str) -> None:
    for iid in self.cart_tree.get_children():
        row_values = self.cart_tree.item(iid, "values")
        if row_values and str(row_values[0]) == str(key):
            self.cart_tree.selection_set(iid)
            self.cart_tree.see(iid)
            break


def decrease_selected_cart_qty(self) -> None:
    selection = self.cart_tree.selection()
    if not selection or not self.sales_manager.current_order:
        return
    values = self.cart_tree.item(selection[0], "values")
    key = str(values[0])
    current_qty = None
    if hasattr(self, "cart_line_qty_entry"):
        try:
            current_qty = int(self.cart_line_qty_entry.get())
        except Exception:
            current_qty = None
    if current_qty is None:
        try:
            current_qty = int(values[2])
        except (ValueError, TypeError):
            return
    new_qty = current_qty - 1
    if self.sales_manager.update_cart_quantity(key, new_qty):
        self.refresh_cart_display()
        self._reselect_cart_row_by_key(key)
        self._on_cart_selection_changed(None)
    else:
        messagebox.showerror("Error", "Invalid quantity")


def increase_selected_cart_qty(self) -> None:
    selection = self.cart_tree.selection()
    if not selection or not self.sales_manager.current_order:
        return
    values = self.cart_tree.item(selection[0], "values")
    key = str(values[0])
    current_qty = None
    if hasattr(self, "cart_line_qty_entry"):
        try:
            current_qty = int(self.cart_line_qty_entry.get())
        except Exception:
            current_qty = None
    if current_qty is None:
        try:
            current_qty = int(values[2])
        except (ValueError, TypeError):
            return
    new_qty = current_qty + 1
    if self.sales_manager.update_cart_quantity(key, new_qty):
        self.refresh_cart_display()
        self._reselect_cart_row_by_key(key)
        self._on_cart_selection_changed(None)
    else:
        messagebox.showerror("Error", "Invalid quantity (exceeds stock)")


def apply_selected_cart_qty_from_entry(self) -> None:
    selection = self.cart_tree.selection()
    if not selection or not self.sales_manager.current_order:
        return
    if not hasattr(self, "cart_line_qty_entry"):
        return
    values = self.cart_tree.item(selection[0], "values")
    key = str(values[0])
    try:
        new_qty = int(self.cart_line_qty_entry.get())
    except ValueError:
        messagebox.showerror("Error", "Invalid quantity")
        return
    if self.sales_manager.update_cart_quantity(key, new_qty):
        self.refresh_cart_display()
        self._reselect_cart_row_by_key(key)
        self._on_cart_selection_changed(None)
    else:
        messagebox.showerror("Error", "Invalid quantity (exceeds stock or not in cart)")


def _cart_quantity_for_key(self, key: str) -> int:
    if not self.sales_manager.current_order:
        return 0
    for item in self.sales_manager.current_order.get_items():
        if item.product.get_product_key() == key:
            return item.quantity
    return 0


def show_cart_product_details(self) -> None:
    selection = self.cart_tree.selection()
    if not selection or not self.sales_manager.current_order:
        return
    values = self.cart_tree.item(selection[0], "values")
    key = str(values[0])
    product = self.store.get_product(key)
    if not product:
        return
    lines: list[str] = [
        f"Type: {product.product_type_name()}",
        f"Name: {product.name}",
        f"ISBN / GTIN: {key}",
        f"Unit price: HKD {product.price:.2f}",
        f"Stock available: {product.stock}",
    ]
    if isinstance(product, Book):
        lines.append(f"Author: {product.author}")
        if product.subtitle:
            lines.append(f"Subtitle: {product.subtitle}")
        if product.publisher:
            lines.append(f"Publisher: {product.publisher}")
        lines.append(f"Category: {product.category}")
        if getattr(product, "subcategory", None):
            lines.append(f"Subcategory: {product.subcategory}")
        if product.pages:
            lines.append(f"Pages: {product.pages}")
        if product.publication_date:
            lines.append(f"Publication: {product.publication_date}")
        if product.subject:
            lines.append(f"Subject: {product.subject}")
    elif isinstance(product, NonBook):
        lines.append(f"Category: {product.category}")
        if getattr(product, "subcategory", None):
            lines.append(f"Subcategory: {product.subcategory}")
        if getattr(product, "brand", ""):
            lines.append(f"Brand: {product.brand}")
        if getattr(product, "model", ""):
            lines.append(f"Model: {product.model}")
    dialog = tk.Toplevel(self.root)
    dialog.title("Item details")
    dialog.geometry("480x420")
    dialog.transient(self.root)
    dialog.columnconfigure(0, weight=1)
    dialog.rowconfigure(0, weight=1)
    info_text = tk.Text(dialog, height=16, width=56, wrap="word", font=("Consolas", 10))
    info_text.grid(row=0, column=0, sticky="nsew", padx=10, pady=(10, 5))
    scroll = ttk.Scrollbar(dialog, command=info_text.yview)
    scroll.grid(row=0, column=1, sticky="ns", pady=(10, 5))
    info_text.config(yscrollcommand=scroll.set)
    info_text.insert("1.0", "\n".join(lines))
    info_text.config(state="disabled")
    btn_frame = ttk.Frame(dialog)
    btn_frame.grid(row=1, column=0, columnspan=2, pady=10)
    ttk.Button(btn_frame, text="Close", command=dialog.destroy).pack(side=tk.LEFT, padx=10)
    center_toplevel(dialog, self.root)


def delete_cart_item(self):
    selection = self.cart_tree.selection()
    if not selection or not self.sales_manager.current_order:
        return
    item_id = selection[0]
    values = self.cart_tree.item(item_id, "values")
    key = str(values[0])
    if self.sales_manager.remove_from_cart(key):
        self.refresh_cart_display()
        self._on_cart_selection_changed(None)
    else:
        messagebox.showerror("Error", "Failed to remove item")


def checkout(self):
    """Process checkout."""
    if not self.sales_manager.current_order or len(self.sales_manager.current_order) == 0:
        messagebox.showerror("Error", "Cart is empty. Add items before checking out.")
        return
    receipt = self.sales_manager.process_checkout()
    if receipt:
        msg = receipt.to_string()

        # Persist the exact same receipt text shown after checkout.
        try:
            payload = receipt.to_dict(include_text=True)
            payload["receipt_text"] = msg
            self.data_manager.append_sale(payload)
        except Exception:
            pass

        # Persist stock and loyalty so Reports / reorder reminder match after restart.
        self.data_manager.save_inventory(self.store._inventory)
        self.data_manager.save_customers(self.store._customers)

        self._show_receipt_dialog(msg)
        self.customer_display_var.set("No customer selected")
        self.refresh_cart_display()
        self.refresh_inventory_display()
        self.refresh_customers_display()
        self.refresh_reports()
        self.refresh_transactions_display()
    else:
        messagebox.showerror(
            "Checkout Failed",
            "Could not complete checkout.\nPossible reason: insufficient stock for one or more items.",
        )
