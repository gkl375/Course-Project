"""
gui.py - Tkinter GUI Interface for Bookstore Management System
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Optional
from models import Store, Customer, Book
from data_manager import DataManager
from sales import SalesManager
from inventory import InventoryManager
from scanner import BarcodeScanner
from api_client import ISBNLookup
import utils


class BookstorePOS:
    """Main GUI application."""
    
    def __init__(self, root: tk.Tk):
        """Initialize GUI."""
        self.root = root
        self.root.title("ABC Bookstore Management System - Hong Kong")
        self.root.geometry("1200x700")
        
        # Initialize backend
        self.store = Store()
        self.data_manager = DataManager()
        self.sales_manager = SalesManager(self.store)
        self.inventory_manager = InventoryManager(self.store)
        
        # Load data
        self.load_data()
        
        # Build GUI
        self.create_widgets()
    
    def create_widgets(self):
        """Create main GUI widgets."""
        # Toolbar
        toolbar = ttk.Frame(self.root)
        toolbar.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
        
        ttk.Label(toolbar, text="📚 ABC Bookstore POS", 
                 font=("Arial", 14, "bold")).pack(side=tk.LEFT)
        
        ttk.Button(toolbar, text="💾 Save", 
                  command=self.save_data).pack(side=tk.RIGHT, padx=5)
        ttk.Button(toolbar, text="⚙️ Settings", 
                  command=self.show_settings).pack(side=tk.RIGHT, padx=5)
        
        # Notebook (tabs)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create tabs
        self.create_sales_tab()
        self.create_inventory_tab()
        self.create_customers_tab()
        self.create_reports_tab()
        self.create_help_tab()
    
    def create_sales_tab(self):
        """Create POS sales tab."""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="🛒 Sales POS")
        
        # Left panel - ISBN input
        left_frame = ttk.LabelFrame(frame, text="Add Items to Cart", padding=10)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        ttk.Label(left_frame, text="ISBN:").grid(row=0, column=0, sticky="w")
        self.isbn_entry = ttk.Entry(left_frame, width=20)
        self.isbn_entry.grid(row=0, column=1, sticky="ew", padx=5)
        
        ttk.Button(left_frame, text="📷 Scan", 
                  command=self.scan_barcode).grid(row=0, column=2, padx=5)
        ttk.Button(left_frame, text="🔍 Search", 
                  command=self.search_and_add).grid(row=0, column=3, padx=5)
        
        ttk.Label(left_frame, text="Quantity:").grid(row=1, column=0, sticky="w")
        self.qty_entry = ttk.Entry(left_frame, width=10)
        self.qty_entry.insert(0, "1")
        self.qty_entry.grid(row=1, column=1, sticky="ew", padx=5)
        
        ttk.Button(left_frame, text="➕ Add to Cart", 
                  command=self.add_to_cart).grid(row=1, column=2, columnspan=2, sticky="ew")
        
        # Cart display
        cart_frame = ttk.LabelFrame(frame, text="Shopping Cart", padding=10)
        cart_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Cart table
        self.cart_tree = ttk.Treeview(cart_frame, 
                                     columns=("Title", "Qty", "Price", "Total"),
                                     height=10)
        self.cart_tree.column("#0", width=0)
        self.cart_tree.column("Title", width=200)
        self.cart_tree.column("Qty", width=50)
        self.cart_tree.column("Price", width=80)
        self.cart_tree.column("Total", width=80)
        
        self.cart_tree.heading("#0", text="")
        self.cart_tree.heading("Title", text="Title")
        self.cart_tree.heading("Qty", text="Qty")
        self.cart_tree.heading("Price", text="Unit Price")
        self.cart_tree.heading("Total", text="Subtotal")
        
        self.cart_tree.pack(fill=tk.BOTH, expand=True)
        
        # Checkout panel
        checkout_frame = ttk.LabelFrame(frame, text="Checkout", padding=10)
        checkout_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(checkout_frame, text="Customer:").grid(row=0, column=0, sticky="w")
        self.customer_combo = ttk.Combobox(checkout_frame, width=30, state="readonly")
        self.customer_combo.grid(row=0, column=1, sticky="ew", padx=5)
        ttk.Button(checkout_frame, text="➕ New", 
                  command=self.add_new_customer).grid(row=0, column=2, padx=5)
        
        ttk.Label(checkout_frame, text="Subtotal:").grid(row=1, column=0, sticky="w")
        self.subtotal_label = ttk.Label(checkout_frame, text="HKD 0.00", 
                                       font=("Arial", 12, "bold"))
        self.subtotal_label.grid(row=1, column=1, sticky="w")
        
        ttk.Label(checkout_frame, text="Discount:").grid(row=2, column=0, sticky="w")
        self.discount_label = ttk.Label(checkout_frame, text="HKD 0.00")
        self.discount_label.grid(row=2, column=1, sticky="w")
        
        ttk.Label(checkout_frame, text="TOTAL:").grid(row=3, column=0, sticky="w")
        self.total_label = ttk.Label(checkout_frame, text="HKD 0.00", 
                                    font=("Arial", 14, "bold"))
        self.total_label.grid(row=3, column=1, sticky="w")
        
        ttk.Button(checkout_frame, text="✓ Checkout", 
                  command=self.checkout).grid(row=0, column=3, rowspan=4, sticky="nsew", padx=5)
        ttk.Button(checkout_frame, text="🔄 Clear", 
                  command=self.clear_cart).grid(row=0, column=4, rowspan=4, sticky="nsew", padx=5)
        
        left_frame.columnconfigure(1, weight=1)
        checkout_frame.columnconfigure(1, weight=1)
        checkout_frame.columnconfigure(3, weight=1)
    
    def create_inventory_tab(self):
        """Create inventory management tab."""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="📚 Inventory")
        
        # Add book section
        add_frame = ttk.LabelFrame(frame, text="Add New Book", padding=10)
        add_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(add_frame, text="ISBN:").grid(row=0, column=0, sticky="w")
        self.add_isbn_entry = ttk.Entry(add_frame, width=20)
        self.add_isbn_entry.grid(row=0, column=1, sticky="ew", padx=5)
        
        ttk.Button(add_frame, text="🔍 Fetch Details", 
                  command=self.fetch_isbn_details).grid(row=0, column=2, padx=5)
        
        ttk.Label(add_frame, text="Title:").grid(row=1, column=0, sticky="w")
        self.add_title_entry = ttk.Entry(add_frame, width=40)
        self.add_title_entry.grid(row=1, column=1, columnspan=2, sticky="ew", padx=5)
        
        ttk.Label(add_frame, text="Author:").grid(row=2, column=0, sticky="w")
        self.add_author_entry = ttk.Entry(add_frame, width=40)
        self.add_author_entry.grid(row=2, column=1, columnspan=2, sticky="ew", padx=5)
        
        ttk.Label(add_frame, text="Price (HKD):").grid(row=3, column=0, sticky="w")
        self.add_price_entry = ttk.Entry(add_frame, width=15)
        self.add_price_entry.grid(row=3, column=1, sticky="ew", padx=5)
        
        ttk.Label(add_frame, text="Stock:").grid(row=4, column=0, sticky="w")
        self.add_stock_entry = ttk.Entry(add_frame, width=15)
        self.add_stock_entry.grid(row=4, column=1, sticky="ew", padx=5)
        
        ttk.Button(add_frame, text="✓ Add Book", 
                  command=self.add_book_to_inventory).grid(row=5, column=0, columnspan=3, sticky="ew", pady=5)
        
        add_frame.columnconfigure(1, weight=1)
        
        # Inventory display
        inv_frame = ttk.LabelFrame(frame, text="Current Inventory", padding=10)
        inv_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.inventory_tree = ttk.Treeview(inv_frame,
                                          columns=("ISBN", "Title", "Author", "Price", "Stock"),
                                          height=15)
        self.inventory_tree.column("#0", width=0)
        self.inventory_tree.column("ISBN", width=130)
        self.inventory_tree.column("Title", width=200)
        self.inventory_tree.column("Author", width=120)
        self.inventory_tree.column("Price", width=80)
        self.inventory_tree.column("Stock", width=60)
        
        self.inventory_tree.heading("ISBN", text="ISBN")
        self.inventory_tree.heading("Title", text="Title")
        self.inventory_tree.heading("Author", text="Author")
        self.inventory_tree.heading("Price", text="Price")
        self.inventory_tree.heading("Stock", text="Stock")
        
        self.inventory_tree.pack(fill=tk.BOTH, expand=True)
        
        self.refresh_inventory_display()
    
    def create_customers_tab(self):
        """Create customer management tab."""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="👥 Customers")
        
        # Customers table
        tree_frame = ttk.LabelFrame(frame, text="Registered Customers", padding=10)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.customers_tree = ttk.Treeview(tree_frame,
                                          columns=("ID", "Name", "Points", "Tier", "Spent"),
                                          height=15)
        self.customers_tree.column("#0", width=0)
        self.customers_tree.column("ID", width=100)
        self.customers_tree.column("Name", width=150)
        self.customers_tree.column("Points", width=80)
        self.customers_tree.column("Tier", width=100)
        self.customers_tree.column("Spent", width=100)
        
        self.customers_tree.heading("ID", text="Customer ID")
        self.customers_tree.heading("Name", text="Name")
        self.customers_tree.heading("Points", text="Points")
        self.customers_tree.heading("Tier", text="Tier")
        self.customers_tree.heading("Spent", text="Total Spent")
        
        self.customers_tree.pack(fill=tk.BOTH, expand=True)
        
        self.refresh_customers_display()
    
    def create_reports_tab(self):
        """Create reports tab."""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="📊 Reports")
        
        # Low stock report
        low_stock_frame = ttk.LabelFrame(frame, text="⚠️ Low Stock Alert (<10 units)", padding=10)
        low_stock_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.low_stock_tree = ttk.Treeview(low_stock_frame,
                                          columns=("Title", "Stock"),
                                          height=10)
        self.low_stock_tree.column("#0", width=0)
        self.low_stock_tree.column("Title", width=400)
        self.low_stock_tree.column("Stock", width=80)
        
        self.low_stock_tree.heading("Title", text="Book Title")
        self.low_stock_tree.heading("Stock", text="Stock")
        
        self.low_stock_tree.pack(fill=tk.BOTH, expand=True)
        
        # Summary stats
        stats_frame = ttk.LabelFrame(frame, text="Summary Statistics", padding=10)
        stats_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(stats_frame, text=f"Total Books: {len(self.store._inventory)}",
                 font=("Arial", 11)).pack(side=tk.LEFT, padx=20)
        
        ttk.Label(stats_frame, text=f"Total Customers: {len(self.store._customers)}",
                 font=("Arial", 11)).pack(side=tk.LEFT, padx=20)
        
        daily_sales = self.store.get_sales_total(1)
        ttk.Label(stats_frame, text=f"Daily Sales: HKD {daily_sales:.2f}",
                 font=("Arial", 11)).pack(side=tk.LEFT, padx=20)
        
        self.refresh_reports()
    
    def create_help_tab(self):
        """Create help tab."""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="❓ Help")
        
        help_text = """
ABC BOOKSTORE MANAGEMENT SYSTEM - User Guide

🛒 SALES POS TAB:
  - Enter ISBN or scan barcode
  - Add to cart with quantity
  - Select customer for loyalty discount
  - Checkout generates receipt

📚 INVENTORY TAB:
  - Enter ISBN and fetch details from database
  - Or add book manually
  - View all books in stock
  - Track prices and quantities

👥 CUSTOMERS TAB:
  - View registered customers
  - Track loyalty points (1pt per HKD10)
  - View customer tiers: Bronze/Silver/Gold

📊 REPORTS TAB:
  - Low stock alerts
  - Daily sales summary
  - Customer statistics

💾 DATA SAVING:
  - All data saved to JSON files in 'data/' directory
  - Data automatically loaded on startup
  - Manual save available in toolbar

🚨 FEATURES:
  ✓ Barcode scanning (webcam or keyboard)
  ✓ ISBN API lookup (Google Books / Open Library)
  ✓ Loyalty discount system (up to 15%)
  ✓ No GST - Hong Kong compliant
  ✓ Professional receipt generation

📧 Support: abc@bookstore.hk
Version 1.0 - 2026
        """
        
        text_widget = tk.Text(frame, wrap=tk.WORD, font=("Courier", 10))
        text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        text_widget.insert(tk.END, help_text.strip())
        text_widget.config(state=tk.DISABLED)
    
    # Helper methods
    def scan_barcode(self):
        """Scan barcode from webcam."""
        isbn = BarcodeScanner.scan_interactive()
        if isbn:
            self.isbn_entry.delete(0, tk.END)
            self.isbn_entry.insert(0, isbn)
            messagebox.showinfo("Success", f"ISBN Scanned: {isbn}")
    
    def search_and_add(self):
        """Search for book by ISBN."""
        isbn = self.isbn_entry.get().strip()
        if not isbn:
            messagebox.showerror("Error", "Enter ISBN")
            return
        
        book = self.store.get_book(isbn)
        if book:
            self.add_to_cart()
        else:
            messagebox.showerror("Not Found", f"ISBN {isbn} not in inventory")
    
    def add_to_cart(self):
        """Add item to cart."""
        isbn = self.isbn_entry.get().strip()
        try:
            qty = int(self.qty_entry.get())
        except ValueError:
            messagebox.showerror("Error", "Invalid quantity")
            return
        
        if self.sales_manager.add_to_cart(isbn, qty):
            self.isbn_entry.delete(0, tk.END)
            self.qty_entry.delete(0, tk.END)
            self.qty_entry.insert(0, "1")
            self.refresh_cart_display()
            messagebox.showinfo("Success", "Added to cart")
        else:
            messagebox.showerror("Error", "Failed to add to cart")
    
    def clear_cart(self):
        """Clear shopping cart."""
        self.sales_manager.cancel_order()
        self.refresh_cart_display()
    
    def refresh_cart_display(self):
        """Refresh cart display."""
        # Clear tree
        for item in self.cart_tree.get_children():
            self.cart_tree.delete(item)
        
        if not self.sales_manager.current_order:
            return
        
        subtotal = 0.0
        for item in self.sales_manager.current_order.get_items():
            subtotal += item.get_subtotal()
            self.cart_tree.insert("", tk.END, values=(
                item.book.name[:40],
                item.quantity,
                f"HKD {item.book.price:.2f}",
                f"HKD {item.get_subtotal():.2f}"
            ))
        
        # Update totals
        self.subtotal_label.config(text=f"HKD {subtotal:.2f}")
        
        discount = 0.0
        if self.sales_manager.current_customer:
            rate = self.sales_manager.current_customer.get_discount_rate()
            discount = subtotal * rate
        
        self.discount_label.config(text=f"HKD {discount:.2f}")
        self.total_label.config(text=f"HKD {subtotal - discount:.2f}")
        
        # Refresh customer combo
        self.refresh_customer_combo()
    
    def refresh_customer_combo(self):
        """Refresh customer dropdown."""
        customers = self.store.get_all_customers()
        display_list = [f"{c.person_id} - {c.name} ({c.get_tier()})" 
                       for c in customers]
        self.customer_combo['values'] = display_list
    
    def add_new_customer(self):
        """Add new customer."""
        dialog = tk.Toplevel(self.root)
        dialog.title("Add New Customer")
        dialog.geometry("300x150")
        
        ttk.Label(dialog, text="Customer Name:").grid(row=0, column=0, sticky="w", padx=10, pady=5)
        name_entry = ttk.Entry(dialog, width=25)
        name_entry.grid(row=0, column=1, padx=10, pady=5)
        
        def save_customer():
            name = name_entry.get().strip()
            if not name:
                messagebox.showerror("Error", "Enter name")
                return
            
            cid = utils.generate_customer_id()
            customer = Customer(name, cid)
            self.store.add_customer(customer)
            messagebox.showinfo("Success", f"Customer {cid} created")
            dialog.destroy()
            self.refresh_customer_combo()
        
        ttk.Button(dialog, text="Save", command=save_customer).grid(row=1, column=0, columnspan=2, sticky="ew", padx=10, pady=10)
    
    def fetch_isbn_details(self):
        """Fetch ISBN details from API."""
        isbn = self.add_isbn_entry.get().strip()
        if not utils.validate_isbn(isbn):
            messagebox.showerror("Error", "Invalid ISBN format (must be 13 digits)")
            return
        
        data = ISBNLookup.fetch_isbn(isbn, self.inventory_manager.isbn_cache)
        if data:
            self.add_title_entry.delete(0, tk.END)
            self.add_title_entry.insert(0, data['title'])
            self.add_author_entry.delete(0, tk.END)
            self.add_author_entry.insert(0, data['authors'])
            messagebox.showinfo("Success", f"Fetched: {data['title']}")
        else:
            messagebox.showerror("Error", f"ISBN {isbn} not found")
    
    def add_book_to_inventory(self):
        """Add book to inventory."""
        isbn = self.add_isbn_entry.get().strip()
        title = self.add_title_entry.get().strip()
        author = self.add_author_entry.get().strip()
        
        try:
            price = float(self.add_price_entry.get())
            stock = int(self.add_stock_entry.get())
        except ValueError:
            messagebox.showerror("Error", "Invalid price or stock")
            return
        
        if not title or not author:
            messagebox.showerror("Error", "Fill all fields")
            return
        
        if self.inventory_manager.add_book_manual(title, isbn, author, price, stock):
            messagebox.showinfo("Success", "Book added")
            # Clear form
            self.add_isbn_entry.delete(0, tk.END)
            self.add_title_entry.delete(0, tk.END)
            self.add_author_entry.delete(0, tk.END)
            self.add_price_entry.delete(0, tk.END)
            self.add_stock_entry.delete(0, tk.END)
            self.refresh_inventory_display()
        else:
            messagebox.showerror("Error", "Failed to add book")
    
    def refresh_inventory_display(self):
        """Refresh inventory table."""
        for item in self.inventory_tree.get_children():
            self.inventory_tree.delete(item)
        
        for book in sorted(self.store._inventory.values(), key=lambda b: b.name):
            self.inventory_tree.insert("", tk.END, values=(
                book.isbn,
                book.name[:40],
                book.author[:30],
                f"HKD {book.price:.2f}",
                f"{book.stock}"
            ))
    
    def refresh_customers_display(self):
        """Refresh customers table."""
        for item in self.customers_tree.get_children():
            self.customers_tree.delete(item)
        
        for cust in sorted(self.store._customers.values(), key=lambda c: c.name):
            self.customers_tree.insert("", tk.END, values=(
                cust.person_id,
                cust.name,
                f"{cust.loyalty_points}",
                cust.get_tier(),
                f"HKD {cust.total_spent:.2f}"
            ))
    
    def refresh_reports(self):
        """Refresh reports."""
        # Low stock
        for item in self.low_stock_tree.get_children():
            self.low_stock_tree.delete(item)
        
        for book in self.store.get_low_stock_books(10):
            self.low_stock_tree.insert("", tk.END, values=(
                book.name[:50],
                f"{book.stock}"
            ))
    
    def checkout(self):
        """Process checkout."""
        if not self.sales_manager.current_order or len(self.sales_manager.current_order) == 0:
            messagebox.showerror("Error", "Cart is empty")
            return
        
        receipt = self.sales_manager.process_checkout()
        if receipt:
            messagebox.showinfo("Receipt", receipt.to_string())
            self.refresh_cart_display()
            self.refresh_inventory_display()
            self.refresh_customers_display()
            self.refresh_reports()
        else:
            messagebox.showerror("Error", "Checkout failed")
    
    def load_data(self):
        """Load data from files."""
        books = self.data_manager.load_inventory()
        for book in books.values():
            self.store.add_book(book)
        
        customers = self.data_manager.load_customers()
        for cust in customers.values():
            self.store.add_customer(cust)
        
        messagebox.showinfo("Load", f"Loaded {len(books)} books, {len(customers)} customers")
    
    def save_data(self):
        """Save data to files."""
        self.data_manager.save_inventory(self.store._inventory)
        self.data_manager.save_customers(self.store._customers)
        messagebox.showinfo("Save", "Data saved successfully")
    
    def show_settings(self):
        """Show settings dialog."""
        messagebox.showinfo("Settings", "Settings coming soon")


if __name__ == "__main__":
    root = tk.Tk()
    app = BookstorePOS(root)
    root.mainloop()
