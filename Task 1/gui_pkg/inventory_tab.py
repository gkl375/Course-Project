"""
Inventory tab (Tkinter): two sub-tabs — books (ISBN, category trees, cover preview)
and non-book items (GTIN, stationery categories, product image). Reorder fields tie
into Product.reorder_level() and the Reports reorder reminder.
"""

import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from tkinter import filedialog

from typing import Optional
from io import BytesIO

import math
import os
import threading
import requests

from PIL import Image, ImageTk

from models import Book, NonBook

from .center_window import center_toplevel


def _preview_reorder_level_from_entries(
    min_stock_entry: tk.Widget,
    lead_entry: tk.Widget,
    avg_entry: tk.Widget,
) -> str:
    """Match ``Product.reorder_level()`` from current entry text (invalid → em dash)."""
    try:
        mn = int(min_stock_entry.get() or "0")
        ld = int(lead_entry.get() or "0")
        avg = float(avg_entry.get() or "0")
        level = float(mn) + float(ld) * float(avg)
        return str(max(0, int(math.ceil(level))))
    except ValueError:
        return "—"


def _preview_reorder_quantity_from_entries(
    min_stock_entry: tk.Widget,
    max_stock_entry: tk.Widget,
) -> str:
    """Match auto PO line qty: max − min (invalid input → em dash)."""
    try:
        mn = int(min_stock_entry.get() or "0")
        mx = int(max_stock_entry.get() or "0")
        return str(mx - mn)
    except ValueError:
        return "—"


def create_inventory_tab(self):
    """Create inventory management tab (Book and Nonbook)."""
    frame = ttk.Frame(self.notebook)
    self.notebook.add(frame, text="📚 Inventory")

    self.inventory_mode_notebook = ttk.Notebook(frame)
    self.inventory_mode_notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    # ========== Book tab: add form + books inventory + cover ==========
    book_tab = ttk.Frame(self.inventory_mode_notebook, padding=5)
    self.inventory_mode_notebook.add(book_tab, text="📖 Book")

    add_book_outer = ttk.LabelFrame(book_tab, text="Add New Book", padding=10)
    add_book_outer.pack(fill=tk.X, pady=(0, 8))

    add_book_frame = ttk.Frame(add_book_outer)
    add_book_frame.pack(fill=tk.X)

    ttk.Label(add_book_frame, text="ISBN:").grid(row=0, column=0, sticky="w")
    self.add_isbn_entry = ttk.Entry(add_book_frame, width=40)
    self.add_isbn_entry.grid(row=0, column=1, sticky="ew", padx=5)

    self.fetch_btn = ttk.Button(
        add_book_frame,
        text="🔍 Fetch Details",
        command=self.fetch_isbn_details,
    )
    self.fetch_btn.grid(row=0, column=2, padx=5)
    self.fetch_status_var = tk.StringVar()
    ttk.Label(
        add_book_frame,
        textvariable=self.fetch_status_var,
        foreground="gray",
    ).grid(row=0, column=3, padx=5, sticky="w")

    ttk.Label(add_book_frame, text="Title:").grid(row=1, column=0, sticky="w")
    self.add_title_entry = ttk.Entry(add_book_frame, width=40)
    self.add_title_entry.grid(row=1, column=1, columnspan=2, sticky="ew", padx=5)

    ttk.Label(add_book_frame, text="Subtitle:").grid(row=2, column=0, sticky="w")
    self.add_subtitle_entry = ttk.Entry(add_book_frame, width=40)
    self.add_subtitle_entry.grid(row=2, column=1, columnspan=2, sticky="ew", padx=5)

    ttk.Label(add_book_frame, text="Author:").grid(row=3, column=0, sticky="w")
    self.add_author_entry = ttk.Entry(add_book_frame, width=40)
    self.add_author_entry.grid(row=3, column=1, columnspan=2, sticky="ew", padx=5)

    ttk.Label(add_book_frame, text="Publisher:").grid(row=4, column=0, sticky="w")
    self.add_publisher_entry = ttk.Entry(add_book_frame, width=40)
    self.add_publisher_entry.grid(row=4, column=1, columnspan=2, sticky="ew", padx=5)

    ttk.Label(add_book_frame, text="Publication Date:").grid(row=5, column=0, sticky="w")
    self.add_pub_date_entry = ttk.Entry(add_book_frame, width=40)
    self.add_pub_date_entry.grid(row=5, column=1, columnspan=2, sticky="ew", padx=5)

    # Book Category / Subcategory - user chooses from Book.BOOK_CATEGORIES
    ttk.Label(add_book_frame, text="Category:").grid(row=6, column=0, sticky="w")
    self.add_subject_entry = ttk.Combobox(add_book_frame, width=40, state="readonly")
    self.add_subject_entry["values"] = list(Book.BOOK_CATEGORIES.keys())
    self.add_subject_entry.grid(row=6, column=1, columnspan=2, sticky="ew", padx=5)
    self.add_subject_entry.bind("<<ComboboxSelected>>", self._on_book_category_selected)

    ttk.Label(add_book_frame, text="Subcategory:").grid(row=7, column=0, sticky="w")
    self.add_book_subcategory_combo = ttk.Combobox(add_book_frame, width=40, state="readonly")
    self.add_book_subcategory_combo.grid(row=7, column=1, columnspan=2, sticky="ew", padx=5)

    ttk.Label(add_book_frame, text="Price (HKD):").grid(row=8, column=0, sticky="w")
    self.add_price_entry = ttk.Entry(add_book_frame, width=40)
    self.add_price_entry.grid(row=8, column=1, columnspan=2, sticky="ew", padx=5)

    ttk.Label(add_book_frame, text="Stock:").grid(row=9, column=0, sticky="w")
    self.add_stock_entry = ttk.Entry(add_book_frame, width=40)
    self.add_stock_entry.grid(row=9, column=1, columnspan=2, sticky="ew", padx=5)

    ttk.Button(
        add_book_frame,
        text="✓ Add Book",
        command=self.add_book_to_inventory,
    ).grid(row=10, column=0, sticky="ew", pady=5)

    ttk.Button(
        add_book_frame,
        text="Search",
        command=self.search_inventory,
    ).grid(row=10, column=1, sticky="ew", pady=5, padx=2)

    ttk.Button(
        add_book_frame,
        text="Clear",
        command=self.clear_inventory_search,
    ).grid(row=10, column=2, sticky="ew", pady=5, padx=2)

    add_book_frame.columnconfigure(1, weight=1)

    inv_book_frame = ttk.LabelFrame(book_tab, text="Current Inventory", padding=10)
    inv_book_frame.pack(fill=tk.BOTH, expand=True)

    book_inv_content = ttk.Frame(inv_book_frame)
    book_inv_content.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

    book_tree_frame = ttk.Frame(book_inv_content)
    book_tree_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    scroll_b = ttk.Scrollbar(book_tree_frame)
    scroll_b.pack(side=tk.RIGHT, fill=tk.Y)

    self.inventory_book_tree = ttk.Treeview(
        book_tree_frame,
        columns=("ISBN", "Title", "Author", "Publisher", "Category", "Subcategory", "Price", "Stock"),
        height=14,
        yscrollcommand=scroll_b.set,
        show="headings",
    )
    scroll_b.config(command=self.inventory_book_tree.yview)

    for col, w in (
        ("ISBN", 110),
        ("Title", 180),
        ("Author", 100),
        ("Publisher", 100),
        ("Category", 110),
        ("Subcategory", 110),
        ("Price", 72),
        ("Stock", 48),
    ):
        self.inventory_book_tree.column(col, width=w)
        self.inventory_book_tree.heading(col, text=col)

    self.inventory_book_tree.bind("<Double-1>", lambda e: self.edit_inventory_item())
    self.inventory_book_tree.bind(
        "<<TreeviewSelect>>",
        lambda e: self._on_inventory_tree_select(self.inventory_book_tree),
    )
    self.inventory_book_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    preview_frame = ttk.LabelFrame(book_inv_content, text="Cover Preview", padding=10)
    preview_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(10, 0))
    preview_frame.config(width=240, height=340)
    preview_frame.pack_propagate(False)

    self.inventory_cover_label = tk.Label(
        preview_frame,
        bd=1,
        relief="solid",
        cursor="hand2",
    )
    self.inventory_cover_label.pack(fill=tk.BOTH, expand=True)
    self.inventory_cover_label.bind("<Button-1>", lambda e: self._open_large_cover_view())

    book_btn_frame = ttk.Frame(inv_book_frame)
    book_btn_frame.pack(fill=tk.X, padx=0, pady=0)
    ttk.Button(
        book_btn_frame,
        text="✏️ Edit Selected",
        command=self.edit_inventory_item,
    ).pack(side=tk.LEFT, padx=5, pady=5)
    ttk.Button(
        book_btn_frame,
        text="🗑️ Delete Selected",
        command=self.delete_inventory_item,
    ).pack(side=tk.LEFT, padx=5, pady=5)

    # ========== Nonbook tab: add form + nonbook inventory ==========
    nb_tab = ttk.Frame(self.inventory_mode_notebook, padding=5)
    self.inventory_mode_notebook.add(nb_tab, text="📎 Nonbook")

    add_nb_outer = ttk.LabelFrame(nb_tab, text="Add New Nonbook", padding=10)
    add_nb_outer.pack(fill=tk.X, pady=(0, 8))
    add_nonbook_frame = ttk.Frame(add_nb_outer)
    add_nonbook_frame.pack(fill=tk.X)

    ttk.Label(add_nonbook_frame, text="Name:").grid(row=0, column=0, sticky="w")
    self.add_nb_name_entry = ttk.Entry(add_nonbook_frame, width=40)
    self.add_nb_name_entry.grid(row=0, column=1, columnspan=2, sticky="ew", padx=5)

    ttk.Label(add_nonbook_frame, text="Brand:").grid(row=1, column=0, sticky="w")
    self.add_nb_brand_entry = ttk.Entry(add_nonbook_frame, width=40)
    self.add_nb_brand_entry.grid(row=1, column=1, columnspan=2, sticky="ew", padx=5)

    ttk.Label(add_nonbook_frame, text="Model:").grid(row=2, column=0, sticky="w")
    self.add_nb_model_entry = ttk.Entry(add_nonbook_frame, width=40)
    self.add_nb_model_entry.grid(row=2, column=1, columnspan=2, sticky="ew", padx=5)

    ttk.Label(add_nonbook_frame, text="GTIN (barcode):").grid(row=3, column=0, sticky="w")
    self.add_nb_gtin_entry = ttk.Entry(add_nonbook_frame, width=40)
    self.add_nb_gtin_entry.grid(row=3, column=1, columnspan=2, sticky="ew", padx=5)

    ttk.Label(add_nonbook_frame, text="Category:").grid(row=4, column=0, sticky="w")
    self.add_nb_category_combo = ttk.Combobox(add_nonbook_frame, width=40, state="readonly")
    self.add_nb_category_combo["values"] = list(NonBook.NONBOOK_CATEGORIES.keys())
    self.add_nb_category_combo.grid(row=4, column=1, columnspan=2, sticky="ew", padx=5)
    self.add_nb_category_combo.bind("<<ComboboxSelected>>", self._on_nb_category_selected)

    ttk.Label(add_nonbook_frame, text="Subcategory:").grid(row=5, column=0, sticky="w")
    self.add_nb_subcategory_combo = ttk.Combobox(add_nonbook_frame, width=40, state="readonly")
    self.add_nb_subcategory_combo.grid(row=5, column=1, columnspan=2, sticky="ew", padx=5)

    ttk.Label(add_nonbook_frame, text="Price (HKD):").grid(row=6, column=0, sticky="w")
    self.add_nb_price_entry = ttk.Entry(add_nonbook_frame, width=40)
    self.add_nb_price_entry.grid(row=6, column=1, columnspan=2, sticky="ew", padx=5)

    ttk.Label(add_nonbook_frame, text="Stock:").grid(row=7, column=0, sticky="w")
    self.add_nb_stock_entry = ttk.Entry(add_nonbook_frame, width=40)
    self.add_nb_stock_entry.grid(row=7, column=1, columnspan=2, sticky="ew", padx=5)

    ttk.Button(
        add_nonbook_frame,
        text="✓ Add Nonbook",
        command=self.add_nonbook_to_inventory,
    ).grid(row=8, column=0, sticky="ew", pady=5)

    ttk.Button(
        add_nonbook_frame,
        text="Search",
        command=self.search_inventory,
    ).grid(row=8, column=1, sticky="ew", pady=5, padx=2)

    ttk.Button(
        add_nonbook_frame,
        text="Clear",
        command=self.clear_inventory_search,
    ).grid(row=8, column=2, sticky="ew", pady=5, padx=2)

    add_nonbook_frame.columnconfigure(1, weight=1)

    inv_nb_frame = ttk.LabelFrame(nb_tab, text="Current Inventory", padding=10)
    inv_nb_frame.pack(fill=tk.BOTH, expand=True)

    nb_inv_content = ttk.Frame(inv_nb_frame)
    nb_inv_content.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

    nb_tree_frame = ttk.Frame(nb_inv_content)
    nb_tree_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    scroll_nb = ttk.Scrollbar(nb_tree_frame)
    scroll_nb.pack(side=tk.RIGHT, fill=tk.Y)

    self.inventory_nonbook_tree = ttk.Treeview(
        nb_tree_frame,
        columns=("GTIN", "Name", "Brand", "Model", "Category", "Subcategory", "Price", "Stock"),
        height=14,
        yscrollcommand=scroll_nb.set,
        show="headings",
    )
    scroll_nb.config(command=self.inventory_nonbook_tree.yview)

    for col, w in (
        ("GTIN", 110),
        ("Name", 160),
        ("Brand", 90),
        ("Model", 90),
        ("Category", 110),
        ("Subcategory", 110),
        ("Price", 72),
        ("Stock", 48),
    ):
        self.inventory_nonbook_tree.column(col, width=w)
        self.inventory_nonbook_tree.heading(col, text=col)

    self.inventory_nonbook_tree.bind("<Double-1>", lambda e: self.edit_inventory_item())
    self.inventory_nonbook_tree.bind(
        "<<TreeviewSelect>>",
        lambda e: self._on_inventory_tree_select(self.inventory_nonbook_tree),
    )
    self.inventory_nonbook_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    nb_preview_frame = ttk.LabelFrame(nb_inv_content, text="Product Preview", padding=10)
    nb_preview_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(10, 0))
    nb_preview_frame.config(width=240, height=340)
    nb_preview_frame.pack_propagate(False)

    self.inventory_nb_preview_label = tk.Label(
        nb_preview_frame,
        bd=1,
        relief="solid",
        cursor="hand2",
    )
    self.inventory_nb_preview_label.pack(fill=tk.BOTH, expand=True)
    self.inventory_nb_preview_label.bind("<Button-1>", lambda e: self._open_large_nonbook_preview())

    nb_btn_frame = ttk.Frame(inv_nb_frame)
    nb_btn_frame.pack(fill=tk.X, padx=0, pady=0)
    ttk.Button(
        nb_btn_frame,
        text="✏️ Edit Selected",
        command=self.edit_inventory_item,
    ).pack(side=tk.LEFT, padx=5, pady=5)
    ttk.Button(
        nb_btn_frame,
        text="🗑️ Delete Selected",
        command=self.delete_inventory_item,
    ).pack(side=tk.LEFT, padx=5, pady=5)

    self.inventory_mode_notebook.bind("<<NotebookTabChanged>>", self._on_inventory_mode_tab_changed)
    self.refresh_inventory_display()
    self._on_inventory_select()


def add_book_to_inventory(self):
    """Add book to inventory."""
    isbn = self.add_isbn_entry.get().strip()
    title = self.add_title_entry.get().strip()
    subtitle = self.add_subtitle_entry.get().strip()
    author = self.add_author_entry.get().strip()
    publisher = self.add_publisher_entry.get().strip()
    pub_date = self.add_pub_date_entry.get().strip()

    # Category / subcategory come from user selections (Book.BOOK_CATEGORIES).
    category = (self.add_subject_entry.get() or "General").strip()
    subcategory = ""
    if hasattr(self, "add_book_subcategory_combo"):
        subcategory = (self.add_book_subcategory_combo.get() or "").strip()

    cover_url = ""
    if getattr(self, "_last_fetched_isbn", None) == isbn:
        cover_url = (getattr(self, "_last_fetched_cover_url", "") or "").strip()
        # If it's still a remote URL, synchronously cache to local.
        if (
            cover_url
            and not os.path.isfile(cover_url)
            and cover_url.startswith(("http://", "https://"))
        ):
            try:
                resp = requests.get(cover_url, timeout=8)
                resp.raise_for_status()
                local_path = self._save_cover_image_bytes(isbn, resp.content)
                cover_url = local_path
                self._last_fetched_cover_url = local_path
            except Exception:
                # Fall back to remote URL if caching fails.
                pass

    try:
        price = float(self.add_price_entry.get())
        stock = int(self.add_stock_entry.get())
    except ValueError:
        messagebox.showerror("Error", "Invalid price or stock")
        return

    if not title or not author:
        messagebox.showerror("Error", "Fill all fields")
        return

    if self.inventory_manager.add_book_manual(
        title,
        isbn,
        author,
        price,
        stock,
        category=category,
        subcategory=subcategory,
        subtitle=subtitle,
        publisher=publisher,
        publication_date=pub_date,
        subject="",
        cover_url=cover_url,
    ):
        messagebox.showinfo("Success", "Book added")
        # Clear form
        self.add_isbn_entry.delete(0, tk.END)
        self.add_title_entry.delete(0, tk.END)
        self.add_subtitle_entry.delete(0, tk.END)
        self.add_author_entry.delete(0, tk.END)
        self.add_publisher_entry.delete(0, tk.END)
        self.add_pub_date_entry.delete(0, tk.END)
        self.add_subject_entry.set("")  # Category combobox
        if hasattr(self, "add_book_subcategory_combo"):
            self.add_book_subcategory_combo.set("")
        self.add_price_entry.delete(0, tk.END)
        self.add_stock_entry.delete(0, tk.END)
        self.refresh_inventory_display()
        self.data_manager.save_inventory(self.store._inventory)
        self.refresh_reports()
    else:
        messagebox.showerror("Error", "Failed to add book")


def _on_nb_category_selected(self, event=None):
    """Update subcategory combobox when Nonbook category changes."""
    cat = self.add_nb_category_combo.get()
    if cat and cat in NonBook.NONBOOK_CATEGORIES:
        subs = NonBook.NONBOOK_CATEGORIES[cat]
        self.add_nb_subcategory_combo["values"] = subs
        self.add_nb_subcategory_combo.set("")


def _on_book_category_selected(self, event=None):
    """Update subcategory combobox when Book category changes."""
    cat = self.add_subject_entry.get()
    if cat and cat in Book.BOOK_CATEGORIES:
        subs = Book.BOOK_CATEGORIES[cat]
        self.add_book_subcategory_combo["values"] = subs
        self.add_book_subcategory_combo.set("")
    else:
        self.add_book_subcategory_combo["values"] = []
        self.add_book_subcategory_combo.set("")


def add_nonbook_to_inventory(self):
    """Add non-book product to inventory."""
    name = self.add_nb_name_entry.get().strip()
    gtin = self.add_nb_gtin_entry.get().strip()
    category = self.add_nb_category_combo.get().strip()
    subcategory = (self.add_nb_subcategory_combo.get() or "").strip()
    brand = (self.add_nb_brand_entry.get() or "").strip()
    model = (self.add_nb_model_entry.get() or "").strip()

    if not name or not gtin or not category:
        messagebox.showerror("Error", "Name, GTIN and Category are required")
        return
    try:
        price = float(self.add_nb_price_entry.get())
        stock = int(self.add_nb_stock_entry.get() or "0")
    except ValueError:
        messagebox.showerror("Error", "Invalid price or stock")
        return

    if self.inventory_manager.add_nonbook_manual(
        name,
        price,
        gtin,
        category,
        subcategory,
        stock,
        brand=brand,
        model=model,
    ):
        messagebox.showinfo("Success", "Nonbook product added")
        self.add_nb_name_entry.delete(0, tk.END)
        self.add_nb_gtin_entry.delete(0, tk.END)
        self.add_nb_category_combo.set("")
        self.add_nb_subcategory_combo.set("")
        self.add_nb_price_entry.delete(0, tk.END)
        self.add_nb_stock_entry.delete(0, tk.END)
        self.add_nb_brand_entry.delete(0, tk.END)
        self.add_nb_model_entry.delete(0, tk.END)
        self.refresh_inventory_display()
        self.data_manager.save_inventory(self.store._inventory)
        self.refresh_reports()
    else:
        messagebox.showerror("Error", "Failed to add (GTIN may already exist)")


def edit_inventory_item(self):
    """Edit selected inventory item (Book or Nonbook)."""
    if self.inventory_book_tree.selection():
        item = self.inventory_book_tree.selection()[0]
        values = self.inventory_book_tree.item(item, "values")
        key = str(values[0]).strip() if values else ""
        book = self.store.get_book(key)
        if not book:
            messagebox.showerror("Error", "Book not found")
            return
        self._edit_book_dialog(book)
        return

    if self.inventory_nonbook_tree.selection():
        item = self.inventory_nonbook_tree.selection()[0]
        values = self.inventory_nonbook_tree.item(item, "values")
        key = str(values[0]).strip() if values else ""
        nb = self.store.get_nonbook(key)
        if not nb:
            messagebox.showerror("Error", "Product not found")
            return
        self._edit_nonbook_dialog(nb)
        return

    messagebox.showwarning("Warning", "Please select an item to edit")


def _edit_book_dialog(self, book: Book):
    """Open edit dialog for a Book."""
    edit_dialog = tk.Toplevel(self.root)
    edit_dialog.title(f"Edit Book - {book.name}")
    edit_dialog.geometry("780x660")
    edit_dialog.minsize(740, 560)
    edit_dialog.transient(self.root)

    ttk.Label(edit_dialog, text="ISBN:").grid(row=0, column=0, sticky="w", padx=10, pady=5)
    isbn_entry = ttk.Entry(edit_dialog, width=36)
    isbn_entry.insert(0, book.isbn)
    isbn_entry.config(state="readonly")
    isbn_entry.grid(row=0, column=1, sticky="ew", padx=10, pady=5)

    ttk.Label(edit_dialog, text="Title:").grid(row=1, column=0, sticky="w", padx=10, pady=5)
    title_entry = ttk.Entry(edit_dialog, width=36)
    title_entry.insert(0, book.name)
    title_entry.grid(row=1, column=1, sticky="ew", padx=10, pady=5)

    ttk.Label(edit_dialog, text="Subtitle:").grid(row=2, column=0, sticky="w", padx=10, pady=5)
    subtitle_entry = ttk.Entry(edit_dialog, width=36)
    subtitle_entry.insert(0, book.subtitle or "")
    subtitle_entry.grid(row=2, column=1, sticky="ew", padx=10, pady=5)

    ttk.Label(edit_dialog, text="Author:").grid(row=3, column=0, sticky="w", padx=10, pady=5)
    author_entry = ttk.Entry(edit_dialog, width=36)
    author_entry.insert(0, book.author)
    author_entry.grid(row=3, column=1, sticky="ew", padx=10, pady=5)

    ttk.Label(edit_dialog, text="Publisher:").grid(row=4, column=0, sticky="w", padx=10, pady=5)
    publisher_entry = ttk.Entry(edit_dialog, width=36)
    publisher_entry.insert(0, book.publisher or "")
    publisher_entry.grid(row=4, column=1, sticky="ew", padx=10, pady=5)

    ttk.Label(edit_dialog, text="Pub Date:").grid(row=5, column=0, sticky="w", padx=10, pady=5)
    pubdate_entry = ttk.Entry(edit_dialog, width=36)
    pubdate_entry.insert(0, book.publication_date or "")
    pubdate_entry.grid(row=5, column=1, sticky="ew", padx=10, pady=5)

    ttk.Label(edit_dialog, text="Category:").grid(row=6, column=0, sticky="w", padx=10, pady=5)
    book_cat_combo = ttk.Combobox(
        edit_dialog, width=32, values=list(Book.BOOK_CATEGORIES.keys()), state="readonly"
    )
    _bc = (book.category or "General").strip()
    if _bc not in Book.BOOK_CATEGORIES:
        _bc = "General"
    book_cat_combo.set(_bc)
    book_cat_combo.grid(row=6, column=1, sticky="ew", padx=10, pady=5)

    ttk.Label(edit_dialog, text="Subcategory:").grid(row=7, column=0, sticky="w", padx=10, pady=5)
    book_subcat_combo = ttk.Combobox(edit_dialog, width=32, state="readonly")
    if _bc in Book.BOOK_CATEGORIES:
        book_subcat_combo["values"] = Book.BOOK_CATEGORIES[_bc]
    else:
        book_subcat_combo["values"] = []
    _sc = (book.subcategory or "").strip()
    _subs = list(book_subcat_combo["values"] or [])
    if _sc in _subs:
        book_subcat_combo.set(_sc)
    elif _subs:
        book_subcat_combo.set(_subs[0])
    else:
        book_subcat_combo.set("")
    book_subcat_combo.grid(row=7, column=1, sticky="ew", padx=10, pady=5)

    def _edit_book_category_changed(_evt=None) -> None:
        c = book_cat_combo.get()
        if c and c in Book.BOOK_CATEGORIES:
            book_subcat_combo["values"] = Book.BOOK_CATEGORIES[c]
            vals = Book.BOOK_CATEGORIES[c]
            cur = book_subcat_combo.get()
            if vals and (not cur or cur not in vals):
                book_subcat_combo.set(vals[0])
            elif not vals:
                book_subcat_combo.set("")
        else:
            book_subcat_combo["values"] = []
            book_subcat_combo.set("")

    book_cat_combo.bind("<<ComboboxSelected>>", _edit_book_category_changed)

    ttk.Label(edit_dialog, text="Price (HKD):").grid(row=8, column=0, sticky="w", padx=10, pady=5)
    price_entry = ttk.Entry(edit_dialog, width=36)
    price_entry.insert(0, str(book.price))
    price_entry.grid(row=8, column=1, sticky="ew", padx=10, pady=5)

    ttk.Label(edit_dialog, text="Stock:").grid(row=9, column=0, sticky="w", padx=10, pady=5)
    stock_entry = ttk.Entry(edit_dialog, width=36)
    stock_entry.insert(0, str(book.stock))
    stock_entry.grid(row=9, column=1, sticky="ew", padx=10, pady=5)

    reorder_enabled_var = tk.BooleanVar(value=bool(getattr(book, "reorder_enabled", False)))
    reorder_cb = ttk.Checkbutton(
        edit_dialog, text="Enable reorder reminder", variable=reorder_enabled_var
    )
    reorder_cb.grid(row=10, column=0, columnspan=2, sticky="w", padx=10, pady=(10, 2))

    ttk.Label(edit_dialog, text="Minimum stock level:").grid(row=11, column=0, sticky="w", padx=10, pady=5)
    min_stock_entry = ttk.Entry(edit_dialog, width=36)
    min_stock_entry.insert(0, str(getattr(book, "minimum_stock_level", 0)))
    min_stock_entry.grid(row=11, column=1, sticky="ew", padx=10, pady=5)

    ttk.Label(edit_dialog, text="Maximum stock level:").grid(row=12, column=0, sticky="w", padx=10, pady=5)
    max_stock_entry = ttk.Entry(edit_dialog, width=36)
    max_stock_entry.insert(0, str(getattr(book, "maximum_stock_level", 0)))
    max_stock_entry.grid(row=12, column=1, sticky="ew", padx=10, pady=5)

    ttk.Label(edit_dialog, text="Lead time (days):").grid(row=13, column=0, sticky="w", padx=10, pady=5)
    lead_entry = ttk.Entry(edit_dialog, width=36)
    lead_entry.insert(0, str(getattr(book, "lead_time_days", 0)))
    lead_entry.grid(row=13, column=1, sticky="ew", padx=10, pady=5)

    ttk.Label(edit_dialog, text="Average daily sales:").grid(row=14, column=0, sticky="w", padx=10, pady=5)
    avg_entry = ttk.Entry(edit_dialog, width=36)
    avg_entry.insert(0, str(getattr(book, "average_daily_sales", 0.0)))
    avg_entry.grid(row=14, column=1, sticky="ew", padx=10, pady=5)

    ttk.Label(edit_dialog, text="Reorder level:").grid(row=15, column=0, sticky="w", padx=10, pady=5)
    reorder_level_lbl = ttk.Label(
        edit_dialog,
        text=_preview_reorder_level_from_entries(min_stock_entry, lead_entry, avg_entry),
        foreground="black",
    )
    reorder_level_lbl.grid(row=15, column=1, sticky="w", padx=10, pady=5)

    ttk.Label(edit_dialog, text="Reorder quantity:").grid(row=16, column=0, sticky="w", padx=10, pady=5)
    reorder_qty_lbl = ttk.Label(
        edit_dialog,
        text=_preview_reorder_quantity_from_entries(min_stock_entry, max_stock_entry),
        foreground="black",
    )
    reorder_qty_lbl.grid(row=16, column=1, sticky="w", padx=10, pady=5)

    ttk.Label(edit_dialog, text="Default supplier:").grid(row=17, column=0, sticky="w", padx=10, pady=5)
    eligible = []
    pkey = str(book.get_product_key())
    for sup in self.store.get_all_suppliers():
        if pkey in sup.catalog_keys:
            eligible.append(f"{sup.person_id} — {sup.name}")
    supplier_combo = ttk.Combobox(edit_dialog, values=eligible, width=32, state="readonly")
    cur_sid = str(getattr(book, "default_supplier_id", "") or "").strip()
    if cur_sid:
        for v in eligible:
            if v.startswith(cur_sid + " — "):
                supplier_combo.set(v)
                break
    supplier_combo.grid(row=17, column=1, sticky="ew", padx=10, pady=5)

    ttk.Label(edit_dialog, text="Cover Image:").grid(row=18, column=0, sticky="w", padx=10, pady=5)
    current_cover = getattr(book, "cover_url", "") or ""
    cover_path_var = tk.StringVar(value=current_cover)
    cover_name = os.path.basename(current_cover) if current_cover else "(none)"
    cover_label = ttk.Label(edit_dialog, text=cover_name, foreground="gray")
    cover_label.grid(row=18, column=1, sticky="w", padx=10, pady=5)

    edit_dialog.columnconfigure(1, weight=1)
    reorder_widgets = [min_stock_entry, max_stock_entry, lead_entry, avg_entry, supplier_combo]

    def _update_reorder_previews(_evt=None) -> None:
        reorder_level_lbl.config(
            text=_preview_reorder_level_from_entries(min_stock_entry, lead_entry, avg_entry)
        )
        reorder_qty_lbl.config(
            text=_preview_reorder_quantity_from_entries(min_stock_entry, max_stock_entry)
        )

    for _e in (min_stock_entry, max_stock_entry, lead_entry, avg_entry):
        _e.bind("<KeyRelease>", _update_reorder_previews, add=True)
        _e.bind("<FocusOut>", _update_reorder_previews, add=True)

    def _refresh_reorder_fields_state():
        is_enabled = reorder_enabled_var.get()
        has_supplier_options = len(eligible) > 0
        if is_enabled and not has_supplier_options:
            reorder_enabled_var.set(False)
            messagebox.showwarning(
                "Reorder reminder",
                "No eligible default supplier for this product.\n"
                "Add this product to a supplier catalog first.",
            )
            is_enabled = False
        for w in reorder_widgets:
            w.config(state=("normal" if is_enabled else "readonly"))

    reorder_cb.config(command=_refresh_reorder_fields_state)
    _refresh_reorder_fields_state()
    _update_reorder_previews()

    def save_changes():
        try:
            book.name = title_entry.get()
            book.subtitle = subtitle_entry.get()
            book.author = author_entry.get()
            book.publisher = publisher_entry.get()
            book.publication_date = pubdate_entry.get()
            book.category = book_cat_combo.get().strip() or "General"
            book.subcategory = (book_subcat_combo.get() or "").strip()
            book.subject = ""
            book.price = float(price_entry.get())
            book.stock = int(stock_entry.get())
            min_stock = int(min_stock_entry.get() or "0")
            max_stock = int(max_stock_entry.get() or "0")
            if min_stock < 0 or max_stock < 0:
                messagebox.showerror(
                    "Error",
                    "Minimum and maximum stock levels cannot be negative.",
                )
                return
            if max_stock < min_stock:
                messagebox.showerror(
                    "Error",
                    "Maximum stock level must be greater than or equal to minimum stock level.",
                )
                return
            chosen_sid = ""
            if supplier_combo.get() and " — " in supplier_combo.get():
                chosen_sid = supplier_combo.get().split(" — ", 1)[0].strip()
            if (
                reorder_enabled_var.get()
                and chosen_sid
                and chosen_sid not in [s.split(" — ", 1)[0].strip() for s in eligible]
            ):
                messagebox.showerror(
                    "Error",
                    "Default supplier must supply this product (exists in supplier catalog).",
                )
                return
            if reorder_enabled_var.get():
                if len(eligible) == 0:
                    messagebox.showerror(
                        "Error",
                        "No eligible default supplier. Add product to supplier catalog first.",
                    )
                    return
                if max_stock <= 0:
                    messagebox.showerror(
                        "Error",
                        "Maximum stock level is required when reorder reminder is enabled.",
                    )
                    return
                if max_stock <= min_stock:
                    messagebox.showerror(
                        "Error",
                        "When reorder reminder is enabled, maximum stock must be greater than minimum "
                        "(reorder quantity = max − min).",
                    )
                    return
                if not chosen_sid:
                    messagebox.showerror("Error", "Please select a default supplier.")
                    return
            book.update_reorder_params(
                minimum_stock_level=min_stock,
                maximum_stock_level=max_stock,
                lead_time_days=int(lead_entry.get() or "0"),
                average_daily_sales=float(avg_entry.get() or "0"),
                default_supplier_id=chosen_sid,
                reorder_enabled=reorder_enabled_var.get(),
            )
            book.cover_url = cover_path_var.get().strip()
            messagebox.showinfo("Success", "Book updated successfully")
            edit_dialog.destroy()
            self.refresh_inventory_display()
            self._on_inventory_select()
            self.data_manager.save_inventory(self.store._inventory)
            self.refresh_reports()
        except ValueError:
            messagebox.showerror("Error", "Invalid price or stock format")

    def import_cover():
        src = filedialog.askopenfilename(
            title="Select Cover Image",
            filetypes=[
                ("Image files", "*.jpg;*.jpeg;*.png;*.gif;*.bmp"),
                ("All files", "*.*"),
            ],
        )
        if not src:
            return
        local_path = self._import_cover_image_from_file(book.isbn, src)
        if local_path:
            cover_path_var.set(local_path)
            cover_label.config(text=os.path.basename(local_path) or "(none)")

    button_frame = ttk.Frame(edit_dialog)
    button_frame.grid(
        row=19, column=0, columnspan=2, sticky="ew", padx=10, pady=(10, 14)
    )
    import_btn = ttk.Button(button_frame, text="Import Cover...", command=import_cover)
    import_btn.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 5))
    save_btn = ttk.Button(button_frame, text="Save Changes", command=save_changes)
    save_btn.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(5, 0))
    center_toplevel(edit_dialog, self.root)


def _edit_nonbook_dialog(self, nb: NonBook):
    """Open edit dialog for a Nonbook."""
    edit_dialog = tk.Toplevel(self.root)
    edit_dialog.title(f"Edit Nonbook - {nb.name}")
    edit_dialog.geometry("780x630")
    edit_dialog.minsize(740, 540)
    edit_dialog.transient(self.root)

    ttk.Label(edit_dialog, text="GTIN:").grid(row=0, column=0, sticky="w", padx=10, pady=5)
    gtin_entry = ttk.Entry(edit_dialog, width=36)
    gtin_entry.insert(0, nb.gtin)
    gtin_entry.config(state="readonly")
    gtin_entry.grid(row=0, column=1, sticky="ew", padx=10, pady=5)

    ttk.Label(edit_dialog, text="Name:").grid(row=1, column=0, sticky="w", padx=10, pady=5)
    name_entry = ttk.Entry(edit_dialog, width=36)
    name_entry.insert(0, nb.name)
    name_entry.grid(row=1, column=1, sticky="ew", padx=10, pady=5)

    ttk.Label(edit_dialog, text="Brand:").grid(row=2, column=0, sticky="w", padx=10, pady=5)
    brand_entry = ttk.Entry(edit_dialog, width=36)
    brand_entry.insert(0, getattr(nb, "brand", "") or "")
    brand_entry.grid(row=2, column=1, sticky="ew", padx=10, pady=5)

    ttk.Label(edit_dialog, text="Category:").grid(row=3, column=0, sticky="w", padx=10, pady=5)
    cat_combo = ttk.Combobox(
        edit_dialog, width=32, values=list(NonBook.NONBOOK_CATEGORIES.keys()), state="readonly"
    )
    _nc = (nb.category or "").strip()
    if _nc not in NonBook.NONBOOK_CATEGORIES:
        _nc = list(NonBook.NONBOOK_CATEGORIES.keys())[0] if NonBook.NONBOOK_CATEGORIES else ""
    cat_combo.set(_nc)
    cat_combo.grid(row=3, column=1, sticky="ew", padx=10, pady=5)

    ttk.Label(edit_dialog, text="Subcategory:").grid(row=4, column=0, sticky="w", padx=10, pady=5)
    subcat_combo = ttk.Combobox(edit_dialog, width=32, state="readonly")
    if _nc in NonBook.NONBOOK_CATEGORIES:
        subcat_combo["values"] = NonBook.NONBOOK_CATEGORIES[_nc]
    else:
        subcat_combo["values"] = []
    _ns = (nb.subcategory or "").strip()
    _ns_list = list(subcat_combo["values"] or [])
    if _ns in _ns_list:
        subcat_combo.set(_ns)
    elif _ns_list:
        subcat_combo.set(_ns_list[0])
    else:
        subcat_combo.set("")
    subcat_combo.grid(row=4, column=1, sticky="ew", padx=10, pady=5)

    def _edit_nb_category_changed(_evt=None) -> None:
        c = cat_combo.get()
        if c and c in NonBook.NONBOOK_CATEGORIES:
            subcat_combo["values"] = NonBook.NONBOOK_CATEGORIES[c]
            vals = NonBook.NONBOOK_CATEGORIES[c]
            cur = subcat_combo.get()
            if vals and (not cur or cur not in vals):
                subcat_combo.set(vals[0])
            elif not vals:
                subcat_combo.set("")
        else:
            subcat_combo["values"] = []
            subcat_combo.set("")

    cat_combo.bind("<<ComboboxSelected>>", _edit_nb_category_changed)

    ttk.Label(edit_dialog, text="Model:").grid(row=5, column=0, sticky="w", padx=10, pady=5)
    model_entry = ttk.Entry(edit_dialog, width=36)
    model_entry.insert(0, getattr(nb, "model", "") or "")
    model_entry.grid(row=5, column=1, sticky="ew", padx=10, pady=5)

    ttk.Label(edit_dialog, text="Price (HKD):").grid(row=6, column=0, sticky="w", padx=10, pady=5)
    price_entry = ttk.Entry(edit_dialog, width=36)
    price_entry.insert(0, str(nb.price))
    price_entry.grid(row=6, column=1, sticky="ew", padx=10, pady=5)

    ttk.Label(edit_dialog, text="Stock:").grid(row=7, column=0, sticky="w", padx=10, pady=5)
    stock_entry = ttk.Entry(edit_dialog, width=36)
    stock_entry.insert(0, str(nb.stock))
    stock_entry.grid(row=7, column=1, sticky="ew", padx=10, pady=5)

    reorder_enabled_var = tk.BooleanVar(value=bool(getattr(nb, "reorder_enabled", False)))
    reorder_cb = ttk.Checkbutton(
        edit_dialog, text="Enable reorder reminder", variable=reorder_enabled_var
    )
    reorder_cb.grid(row=8, column=0, columnspan=2, sticky="w", padx=10, pady=(10, 2))

    ttk.Label(edit_dialog, text="Minimum stock level:").grid(row=9, column=0, sticky="w", padx=10, pady=5)
    min_stock_entry = ttk.Entry(edit_dialog, width=36)
    min_stock_entry.insert(0, str(getattr(nb, "minimum_stock_level", 0)))
    min_stock_entry.grid(row=9, column=1, sticky="ew", padx=10, pady=5)

    ttk.Label(edit_dialog, text="Maximum stock level:").grid(row=10, column=0, sticky="w", padx=10, pady=5)
    max_stock_entry = ttk.Entry(edit_dialog, width=36)
    max_stock_entry.insert(0, str(getattr(nb, "maximum_stock_level", 0)))
    max_stock_entry.grid(row=10, column=1, sticky="ew", padx=10, pady=5)

    ttk.Label(edit_dialog, text="Lead time (days):").grid(row=11, column=0, sticky="w", padx=10, pady=5)
    lead_entry = ttk.Entry(edit_dialog, width=36)
    lead_entry.insert(0, str(getattr(nb, "lead_time_days", 0)))
    lead_entry.grid(row=11, column=1, sticky="ew", padx=10, pady=5)

    ttk.Label(edit_dialog, text="Average daily sales:").grid(row=12, column=0, sticky="w", padx=10, pady=5)
    avg_entry = ttk.Entry(edit_dialog, width=36)
    avg_entry.insert(0, str(getattr(nb, "average_daily_sales", 0.0)))
    avg_entry.grid(row=12, column=1, sticky="ew", padx=10, pady=5)

    ttk.Label(edit_dialog, text="Reorder level:").grid(row=13, column=0, sticky="w", padx=10, pady=5)
    reorder_level_lbl = ttk.Label(
        edit_dialog,
        text=_preview_reorder_level_from_entries(min_stock_entry, lead_entry, avg_entry),
        foreground="black",
    )
    reorder_level_lbl.grid(row=13, column=1, sticky="w", padx=10, pady=5)

    ttk.Label(edit_dialog, text="Reorder quantity:").grid(row=14, column=0, sticky="w", padx=10, pady=5)
    reorder_qty_lbl = ttk.Label(
        edit_dialog,
        text=_preview_reorder_quantity_from_entries(min_stock_entry, max_stock_entry),
        foreground="black",
    )
    reorder_qty_lbl.grid(row=14, column=1, sticky="w", padx=10, pady=5)

    ttk.Label(edit_dialog, text="Default supplier:").grid(row=15, column=0, sticky="w", padx=10, pady=5)
    eligible = []
    pkey = str(nb.get_product_key())
    for sup in self.store.get_all_suppliers():
        if pkey in sup.catalog_keys:
            eligible.append(f"{sup.person_id} — {sup.name}")
    supplier_combo = ttk.Combobox(edit_dialog, values=eligible, width=32, state="readonly")
    cur_sid = str(getattr(nb, "default_supplier_id", "") or "").strip()
    if cur_sid:
        for v in eligible:
            if v.startswith(cur_sid + " — "):
                supplier_combo.set(v)
                break
    supplier_combo.grid(row=15, column=1, sticky="ew", padx=10, pady=5)
    edit_dialog.columnconfigure(1, weight=1)

    ttk.Label(edit_dialog, text="Product image:").grid(row=16, column=0, sticky="w", padx=10, pady=5)
    product_image_var = tk.StringVar(value=(getattr(nb, "product_image", "") or "").strip())
    pi_display = os.path.basename(product_image_var.get()) if product_image_var.get() else "(none)"
    product_img_label = ttk.Label(edit_dialog, text=pi_display, foreground="gray")
    product_img_label.grid(row=16, column=1, sticky="w", padx=10, pady=5)

    reorder_widgets = [min_stock_entry, max_stock_entry, lead_entry, avg_entry, supplier_combo]

    def _update_reorder_previews(_evt=None) -> None:
        reorder_level_lbl.config(
            text=_preview_reorder_level_from_entries(min_stock_entry, lead_entry, avg_entry)
        )
        reorder_qty_lbl.config(
            text=_preview_reorder_quantity_from_entries(min_stock_entry, max_stock_entry)
        )

    for _e in (min_stock_entry, max_stock_entry, lead_entry, avg_entry):
        _e.bind("<KeyRelease>", _update_reorder_previews, add=True)
        _e.bind("<FocusOut>", _update_reorder_previews, add=True)

    def _refresh_reorder_fields_state():
        is_enabled = reorder_enabled_var.get()
        has_supplier_options = len(eligible) > 0
        if is_enabled and not has_supplier_options:
            reorder_enabled_var.set(False)
            messagebox.showwarning(
                "Reorder reminder",
                "No eligible default supplier for this product.\n"
                "Add this product to a supplier catalog first.",
            )
            is_enabled = False
        for w in reorder_widgets:
            w.config(state=("normal" if is_enabled else "readonly"))

    reorder_cb.config(command=_refresh_reorder_fields_state)
    _refresh_reorder_fields_state()
    _update_reorder_previews()

    def save_changes():
        try:
            nb.name = name_entry.get()
            nb.brand = brand_entry.get().strip()
            nb.model = model_entry.get().strip()
            nb.category = cat_combo.get()
            nb.subcategory = subcat_combo.get() or ""
            nb.price = float(price_entry.get())
            nb.stock = int(stock_entry.get())
            min_stock = int(min_stock_entry.get() or "0")
            max_stock = int(max_stock_entry.get() or "0")
            if min_stock < 0 or max_stock < 0:
                messagebox.showerror(
                    "Error",
                    "Minimum and maximum stock levels cannot be negative.",
                )
                return
            if max_stock < min_stock:
                messagebox.showerror(
                    "Error",
                    "Maximum stock level must be greater than or equal to minimum stock level.",
                )
                return
            chosen_sid = ""
            if supplier_combo.get() and " — " in supplier_combo.get():
                chosen_sid = supplier_combo.get().split(" — ", 1)[0].strip()
            if (
                reorder_enabled_var.get()
                and chosen_sid
                and chosen_sid not in [s.split(" — ", 1)[0].strip() for s in eligible]
            ):
                messagebox.showerror(
                    "Error", "Default supplier must supply this product (exists in supplier catalog)."
                )
                return
            if reorder_enabled_var.get():
                if len(eligible) == 0:
                    messagebox.showerror(
                        "Error",
                        "No eligible default supplier. Add product to supplier catalog first.",
                    )
                    return
                if max_stock <= 0:
                    messagebox.showerror(
                        "Error",
                        "Maximum stock level is required when reorder reminder is enabled.",
                    )
                    return
                if max_stock <= min_stock:
                    messagebox.showerror(
                        "Error",
                        "When reorder reminder is enabled, maximum stock must be greater than minimum "
                        "(reorder quantity = max − min).",
                    )
                    return
                if not chosen_sid:
                    messagebox.showerror("Error", "Please select a default supplier.")
                    return
            nb.update_reorder_params(
                minimum_stock_level=min_stock,
                maximum_stock_level=max_stock,
                lead_time_days=int(lead_entry.get() or "0"),
                average_daily_sales=float(avg_entry.get() or "0"),
                default_supplier_id=chosen_sid,
                reorder_enabled=reorder_enabled_var.get(),
            )
            nb.product_image = product_image_var.get().strip()
            messagebox.showinfo("Success", "Nonbook updated successfully")
            edit_dialog.destroy()
            self.refresh_inventory_display()
            self._on_inventory_select()
            self.data_manager.save_inventory(self.store._inventory)
            self.refresh_reports()
        except ValueError:
            messagebox.showerror("Error", "Invalid price or stock format")

    def import_nb_product_image() -> None:
        src = filedialog.askopenfilename(
            title="Select Product Image",
            filetypes=[
                ("Image files", "*.jpg;*.jpeg;*.png;*.gif;*.bmp"),
                ("All files", "*.*"),
            ],
        )
        if not src:
            return
        local_path = self._import_nonbook_product_image_from_file(nb.gtin, src)
        if local_path:
            product_image_var.set(local_path)
            product_img_label.config(text=os.path.basename(local_path) or "(none)")

    button_frame = ttk.Frame(edit_dialog)
    button_frame.grid(
        row=17, column=0, columnspan=2, sticky="ew", padx=10, pady=(10, 14)
    )
    import_btn = ttk.Button(
        button_frame, text="Import Product Image...", command=import_nb_product_image
    )
    import_btn.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 5))
    save_btn = ttk.Button(button_frame, text="Save Changes", command=save_changes)
    save_btn.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(5, 0))
    center_toplevel(edit_dialog, self.root)


def delete_inventory_item(self):
    """Delete selected inventory item (Book or Nonbook)."""
    if self.inventory_book_tree.selection():
        item = self.inventory_book_tree.selection()[0]
        values = self.inventory_book_tree.item(item, "values")
        if not values or len(values) < 2:
            messagebox.showerror("Error", "Invalid selection")
            return
        key = str(values[0]).strip()
        title = values[1]
    elif self.inventory_nonbook_tree.selection():
        item = self.inventory_nonbook_tree.selection()[0]
        values = self.inventory_nonbook_tree.item(item, "values")
        if not values or len(values) < 2:
            messagebox.showerror("Error", "Invalid selection")
            return
        key = str(values[0]).strip()
        title = values[1]
    else:
        messagebox.showwarning("Warning", "Please select an item to delete")
        return

    if messagebox.askyesno(
        "Confirm Delete",
        f"Delete '{title}'?\n\nKey: {key}\n\nThis action cannot be undone.",
    ):
        if self.inventory_manager.delete_product(key):
            messagebox.showinfo("Success", "Item deleted successfully")
            self.refresh_inventory_display()
            self._on_inventory_select()
            self.data_manager.save_inventory(self.store._inventory)
            self.refresh_reports()
        else:
            messagebox.showerror("Error", "Failed to delete item")


def _get_cover_dir(self) -> str:
    """Return directory path for cached cover images."""
    return os.path.join("data", "covers")


def _ensure_cover_dir(self) -> None:
    """Ensure cover cache directory exists."""
    os.makedirs(self._get_cover_dir(), exist_ok=True)


def _cover_path_for_isbn(self, isbn: str) -> str:
    """Canonical local cover path for a given ISBN."""
    safe_isbn = str(isbn).strip().replace("/", "_").replace("\\", "_")
    return os.path.join(self._get_cover_dir(), f"{safe_isbn}.jpg")


def _save_cover_image_bytes(self, isbn: str, content: bytes) -> str:
    """Save raw image bytes as a local cover file and return its path."""
    self._ensure_cover_dir()
    img = Image.open(BytesIO(content))
    img = img.convert("RGB")
    path = self._cover_path_for_isbn(isbn)
    img.save(path, format="JPEG")
    return path


def _import_cover_image_from_file(self, isbn: str, src_path: str) -> Optional[str]:
    """Import a user-selected image file as the cover for an ISBN."""
    try:
        self._ensure_cover_dir()
        img = Image.open(src_path)
        img = img.convert("RGB")
        path = self._cover_path_for_isbn(isbn)
        img.save(path, format="JPEG")
        return path
    except Exception as e:
        messagebox.showerror("Error", f"Failed to import image:\n{e}")
        return None


def _nonbook_image_path_for_gtin(self, gtin: str) -> str:
    """Canonical local path for a Nonbook product image."""
    safe = str(gtin).strip().replace("/", "_").replace("\\", "_")
    return os.path.join(self._get_cover_dir(), f"nb_{safe}.jpg")


def _import_nonbook_product_image_from_file(
    self, gtin: str, src_path: str
) -> Optional[str]:
    """Import a user-selected image file as the product preview for a GTIN."""
    try:
        self._ensure_cover_dir()
        img = Image.open(src_path)
        img = img.convert("RGB")
        path = self._nonbook_image_path_for_gtin(gtin)
        img.save(path, format="JPEG")
        return path
    except Exception as e:
        messagebox.showerror("Error", f"Failed to import image:\n{e}")
        return None


def _open_large_cover_view(self):
    """Open a separate window showing a larger version of the current cover (Book only)."""
    isbn = self._current_cover_isbn
    if not isbn:
        selection = self.inventory_book_tree.selection()
        if not selection:
            messagebox.showinfo("Cover", "Select a book in the inventory first.")
            return
        item = selection[0]
        values = self.inventory_book_tree.item(item).get("values") or []
        if len(values) < 1:
            messagebox.showinfo("Cover", "Select a book in the inventory first.")
            return
        isbn = str(values[0]).strip()

    book = self.store.get_book(isbn)
    if not book:
        messagebox.showinfo("Cover", "Book not found for the selected cover.")
        return

    cover_url = (book.cover_url or "").strip()
    if not cover_url:
        messagebox.showinfo("Cover", "This book has no cover image.")
        return

    # Ensure we have a local image path (prefer cached file)
    local_path = cover_url
    if not os.path.isfile(local_path):
        # Try downloading once and caching
        try:
            resp = requests.get(cover_url, timeout=10)
            resp.raise_for_status()
            local_path = self._save_cover_image_bytes(book.isbn, resp.content)
        except Exception as e:
            messagebox.showerror("Cover", f"Failed to load cover image:\n{e}")
            return

    try:
        img = Image.open(local_path)
        img = img.convert("RGB")

        # Create a window sized to fit the full image on screen (no cropping),
        # and freely scale up smaller images.
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()

        w, h = img.size
        if w <= 0 or h <= 0:
            raise ValueError("Invalid image size")

        # Leave some margin around the window, and scale image (up or down)
        max_w = int(screen_w * 0.8)
        max_h = int(screen_h * 0.85)
        scale = min(max_w / w, max_h / h)

        if scale != 1.0:
            new_w, new_h = int(w * scale), int(h * scale)
            img = img.resize((new_w, new_h), Image.LANCZOS)
            w, h = new_w, new_h

        win_w = w + 40
        win_h = h + 80

        viewer = tk.Toplevel(self.root)
        viewer.title(f"Cover - {book.name}")
        viewer.geometry(f"{win_w}x{win_h}")
        viewer.transient(self.root)

        photo = ImageTk.PhotoImage(img)
        self._large_cover_photo = photo

        lbl = tk.Label(viewer, image=photo)
        lbl.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)
        center_toplevel(viewer, self.root)
    except Exception as e:
        messagebox.showerror("Cover", f"Failed to open large cover view:\n{e}")


def _open_large_nonbook_preview(self) -> None:
    """Open a larger view of the Nonbook product image (if any)."""
    gtin = self._current_nonbook_gtin
    if not gtin:
        selection = self.inventory_nonbook_tree.selection()
        if not selection:
            messagebox.showinfo("Preview", "Select a Nonbook item first.")
            return
        values = self.inventory_nonbook_tree.item(selection[0]).get("values") or []
        if len(values) < 1:
            messagebox.showinfo("Preview", "Select a Nonbook item first.")
            return
        gtin = str(values[0]).strip()

    nb = self.store.get_nonbook(gtin)
    if not nb:
        messagebox.showinfo("Preview", "Product not found.")
        return

    path = (getattr(nb, "product_image", "") or "").strip()
    if not path or not os.path.isfile(path):
        messagebox.showinfo("Preview", "No product image. Use Edit → Import to add one.")
        return

    try:
        img = Image.open(path).convert("RGB")
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        w, h = img.size
        if w <= 0 or h <= 0:
            raise ValueError("Invalid image size")

        max_w = int(screen_w * 0.8)
        max_h = int(screen_h * 0.85)
        scale = min(max_w / w, max_h / h)
        if scale != 1.0:
            img = img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)

        viewer = tk.Toplevel(self.root)
        viewer.title(f"Product - {nb.name}")
        viewer.transient(self.root)
        photo = ImageTk.PhotoImage(img)
        self._large_nb_photo = photo
        lbl = tk.Label(viewer, image=photo)
        lbl.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)
        center_toplevel(viewer, self.root)
    except Exception as e:
        messagebox.showerror("Preview", f"Failed to open image:\n{e}")


def _on_inventory_mode_tab_changed(self, event=None) -> None:
    """Clear selection in the hidden inventory table when switching Book / Nonbook tabs."""
    idx = self.inventory_mode_notebook.index(self.inventory_mode_notebook.select())
    if idx == 0:
        nb_sel = self.inventory_nonbook_tree.selection()
        if nb_sel:
            self.inventory_nonbook_tree.selection_remove(*nb_sel)
    else:
        b_sel = self.inventory_book_tree.selection()
        if b_sel:
            self.inventory_book_tree.selection_remove(*b_sel)
    self._on_inventory_select()


def _on_inventory_tree_select(self, source: ttk.Treeview) -> None:
    """Keep a single selection across Books / Nonbooks tables."""
    if source == self.inventory_book_tree:
        nb_sel = self.inventory_nonbook_tree.selection()
        if nb_sel:
            self.inventory_nonbook_tree.selection_remove(*nb_sel)
    else:
        b_sel = self.inventory_book_tree.selection()
        if b_sel:
            self.inventory_book_tree.selection_remove(*b_sel)
    self._on_inventory_select()


def _on_inventory_select(self):
    """Update Book cover preview and Nonbook product preview from current tree selections."""
    if self.inventory_book_tree.selection():
        item = self.inventory_book_tree.selection()[0]
        values = self.inventory_book_tree.item(item).get("values") or []
        if not values:
            self._set_cover_preview(None, "Select an item to preview")
        else:
            key = str(values[0]).strip()
            self._current_cover_isbn = key
            book = self.store.get_book(key)
            if not book:
                self._set_cover_preview(None, "Book not found")
            else:
                self._load_and_show_cover_async(book)
    else:
        self._current_cover_isbn = None
        self._set_cover_preview(None, "Select an item to preview")

    if self.inventory_nonbook_tree.selection():
        item = self.inventory_nonbook_tree.selection()[0]
        values = self.inventory_nonbook_tree.item(item).get("values") or []
        key = str(values[0]).strip() if values else ""
        self._current_nonbook_gtin = key or None
        nb = self.store.get_nonbook(key) if key else None
        if not nb:
            self._set_nonbook_preview(None, "Product not found")
        else:
            self._load_and_show_nonbook_preview_async(nb)
    else:
        self._current_nonbook_gtin = None
        self._set_nonbook_preview(None, "Select an item to preview")


def _set_cover_preview(self, photo: Optional[ImageTk.PhotoImage], text: str):
    """Set cover preview widgets (must be called on main thread)."""
    if photo is None:
        self.inventory_cover_label.config(
            image="",
            text=text or "No Cover",
            justify="center",
            wraplength=220,
        )
        self._inventory_cover_photo = None
    else:
        self.inventory_cover_label.config(image=photo, text="")
        self._inventory_cover_photo = photo  # prevent GC


def _set_nonbook_preview(self, photo: Optional[ImageTk.PhotoImage], text: str):
    """Set Nonbook product preview (image or text summary)."""
    if not hasattr(self, "inventory_nb_preview_label"):
        return
    if photo is None:
        self.inventory_nb_preview_label.config(
            image="",
            text=text or "No preview",
            justify="center",
            wraplength=220,
        )
        self._inventory_nb_preview_photo = None
    else:
        self.inventory_nb_preview_label.config(image=photo, text="")
        self._inventory_nb_preview_photo = photo


def _nonbook_preview_summary_text(self, nb: NonBook) -> str:
    """Short text summary for Nonbook when no image is available."""
    lines = [nb.name, f"GTIN: {nb.gtin}"]
    if getattr(nb, "brand", ""):
        lines.append(f"Brand: {nb.brand}")
    if getattr(nb, "model", ""):
        lines.append(f"Model: {nb.model}")
    cat = f"{nb.category}" + (f" / {nb.subcategory}" if getattr(nb, "subcategory", "") else "")
    lines.append(cat)
    lines.append(f"HKD {nb.price:.2f}  ·  Stock: {nb.stock}")
    return "\n".join(lines)


def _load_and_show_cover_async(self, book: Book):
    """Fetch cover image (if any) without blocking UI."""
    title = f"{book.name}\n{book.author}".strip()
    cover_url = (book.cover_url or "").strip()

    if not cover_url:
        self._set_cover_preview(None, f"{title}\n\n(No cover URL)")
        return

    cached = self._cover_image_cache.get(cover_url)
    if cached:
        self._set_cover_preview(cached, title)
        return

    self._inventory_cover_req_id += 1
    req_id = self._inventory_cover_req_id
    self._set_cover_preview(None, f"{title}\n\nLoading cover...")

    def worker():
        photo: Optional[ImageTk.PhotoImage] = None
        err: Optional[str] = None
        try:
            # Prefer local file path if cover_url points to an existing file
            img = None
            if os.path.isfile(cover_url):
                img = Image.open(cover_url)
            else:
                resp = requests.get(cover_url, timeout=6)
                resp.raise_for_status()
                img = Image.open(BytesIO(resp.content))

            img = img.convert("RGB")
            # Scale the full cover to fit the preview box (letterbox-style; no crop),
            # using 90% of the box so a small margin avoids a visually “clipped” edge.
            box_w, box_h = 240, 340
            w, h = img.size
            if w > 0 and h > 0:
                scale = min(box_w / w, box_h / h) * 0.9  # margin inside preview frame
                if scale != 1.0:
                    new_w, new_h = int(w * scale), int(h * scale)
                    img = img.resize((new_w, new_h), Image.LANCZOS)
            photo = ImageTk.PhotoImage(img)
        except Exception as e:
            err = str(e)

        def apply_result():
            if req_id != self._inventory_cover_req_id:
                return  # outdated request
            if photo is None:
                self._set_cover_preview(None, f"{title}\n\nFailed to load cover:\n{err}")
                return
            self._cover_image_cache[cover_url] = photo
            self._set_cover_preview(photo, title)

        self.root.after(0, apply_result)

    threading.Thread(target=worker, daemon=True).start()


def _load_and_show_nonbook_preview_async(self, nb: NonBook) -> None:
    """Load product image for Nonbook preview without blocking the UI."""
    path = (getattr(nb, "product_image", "") or "").strip()
    summary = self._nonbook_preview_summary_text(nb)

    if not path or not os.path.isfile(path):
        self._set_nonbook_preview(
            None,
            summary + "\n\n(No product image)\nEdit item to import.",
        )
        return

    self._inventory_nb_req_id += 1
    req_id = self._inventory_nb_req_id
    self._set_nonbook_preview(None, summary + "\n\nLoading image...")

    def worker() -> None:
        photo: Optional[ImageTk.PhotoImage] = None
        err: Optional[str] = None
        try:
            img = Image.open(path).convert("RGB")
            box_w, box_h = 240, 340
            w, h = img.size
            if w > 0 and h > 0:
                scale = min(box_w / w, box_h / h) * 0.9
                if scale != 1.0:
                    img = img.resize(
                        (int(w * scale), int(h * scale)),
                        Image.LANCZOS,
                    )
            photo = ImageTk.PhotoImage(img)
        except Exception as e:
            err = str(e)

        def apply_result() -> None:
            if req_id != self._inventory_nb_req_id:
                return
            if photo is None:
                self._set_nonbook_preview(
                    None,
                    summary + f"\n\nFailed to load image:\n{err}",
                )
            else:
                self._set_nonbook_preview(photo, summary)

        self.root.after(0, apply_result)

    threading.Thread(target=worker, daemon=True).start()


def refresh_inventory_display(self) -> None:
    """Refresh inventory tables (Books and Nonbooks), with optional search filter."""
    for item in self.inventory_book_tree.get_children():
        self.inventory_book_tree.delete(item)
    for item in self.inventory_nonbook_tree.get_children():
        self.inventory_nonbook_tree.delete(item)

    products = self.store.get_all_products()
    ptype = getattr(self, "_inventory_search_product_type", None)
    if ptype == "Book":
        products = [p for p in products if isinstance(p, Book)]
    elif ptype == "Nonbook":
        products = [p for p in products if isinstance(p, NonBook)]

    query = getattr(self, "_inventory_search_query", "").strip().lower()
    if query:
        def matches(p) -> bool:
            key = p.get_product_key()
            fields = [p.name, key, p.product_type_name()]
            if isinstance(p, Book):
                fields += [
                    p.author,
                    getattr(p, "publisher", ""),
                    getattr(p, "category", ""),
                    getattr(p, "subcategory", ""),
                ]
            else:
                fields += [
                    getattr(p, "category", ""),
                    getattr(p, "subcategory", ""),
                    getattr(p, "brand", ""),
                    getattr(p, "model", ""),
                ]
            return any(query in (str(f or "")).lower() for f in fields)

        products = [p for p in products if matches(p)]

    books = [p for p in products if isinstance(p, Book)]
    nonbooks = [p for p in products if isinstance(p, NonBook)]

    for b in sorted(books, key=lambda x: str(x.get_product_key())):
        self.inventory_book_tree.insert(
            "",
            tk.END,
            values=(
                str(b.isbn)[:80],
                (b.name or "")[:80],
                (b.author or "")[:80],
                (b.publisher or "")[:80],
                (b.category or "")[:80],
                (b.subcategory or "")[:80],
                f"HKD {b.price:.2f}",
                f"{b.stock}",
            ),
        )

    for nb in sorted(nonbooks, key=lambda x: str(x.get_product_key())):
        self.inventory_nonbook_tree.insert(
            "",
            tk.END,
            values=(
                str(nb.gtin)[:80],
                (nb.name or "")[:80],
                str(getattr(nb, "brand", "") or "")[:80],
                str(getattr(nb, "model", "") or "")[:80],
                (nb.category or "")[:80],
                (nb.subcategory or "")[:80],
                f"HKD {nb.price:.2f}",
                f"{nb.stock}",
            ),
        )


def search_inventory(self) -> None:
    """Apply filter to inventory table using current Add Product inputs.
    Uses only the active tab's fields: Book tab filters Books, Nonbook tab filters Nonbooks.
    """
    parts: list[str] = []
    current_tab = self.inventory_mode_notebook.index(
        self.inventory_mode_notebook.select()
    )
    if current_tab == 0:
        self._inventory_search_product_type = "Book"
        for val in [
            getattr(self.add_isbn_entry, "get", lambda: "")().strip(),
            getattr(self.add_title_entry, "get", lambda: "")().strip(),
            getattr(self.add_author_entry, "get", lambda: "")().strip(),
            getattr(self.add_subject_entry, "get", lambda: "")().strip(),
            getattr(self.add_book_subcategory_combo, "get", lambda: "")().strip(),
        ]:
            if val:
                parts.append(val)
    else:
        self._inventory_search_product_type = "Nonbook"
        for val in [
            getattr(self.add_nb_name_entry, "get", lambda: "")().strip(),
            getattr(self.add_nb_brand_entry, "get", lambda: "")().strip(),
            getattr(self.add_nb_model_entry, "get", lambda: "")().strip(),
            getattr(self.add_nb_gtin_entry, "get", lambda: "")().strip(),
            getattr(self.add_nb_category_combo, "get", lambda: "")().strip(),
            getattr(self.add_nb_subcategory_combo, "get", lambda: "")().strip(),
        ]:
            if val:
                parts.append(val)
    self._inventory_search_query = " ".join(parts)
    self.refresh_inventory_display()


def clear_inventory_search(self) -> None:
    """Clear inventory search filter and reset Add Product inputs."""
    # Clear Book inputs
    self.add_isbn_entry.delete(0, tk.END)
    self.add_title_entry.delete(0, tk.END)
    self.add_subtitle_entry.delete(0, tk.END)
    self.add_author_entry.delete(0, tk.END)
    self.add_publisher_entry.delete(0, tk.END)
    self.add_pub_date_entry.delete(0, tk.END)
    self.add_subject_entry.set("")  # category
    self.add_book_subcategory_combo.set("")
    self.add_price_entry.delete(0, tk.END)
    self.add_stock_entry.delete(0, tk.END)

    # Clear Nonbook inputs
    self.add_nb_name_entry.delete(0, tk.END)
    self.add_nb_brand_entry.delete(0, tk.END)
    self.add_nb_model_entry.delete(0, tk.END)
    self.add_nb_gtin_entry.delete(0, tk.END)
    self.add_nb_category_combo.set("")
    self.add_nb_subcategory_combo.set("")
    self.add_nb_price_entry.delete(0, tk.END)
    self.add_nb_stock_entry.delete(0, tk.END)

    # Clear filter
    self._inventory_search_query = ""
    self._inventory_search_product_type = None
    self.refresh_inventory_display()

