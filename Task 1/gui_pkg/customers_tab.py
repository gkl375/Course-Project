"""
customers_tab.py - Extracted Customers tab UI & logic from gui.py.
"""

import tkinter as tk
from tkinter import ttk, messagebox

import utils
from models import Customer

from .center_window import center_toplevel, style_popup_window


def create_customers_tab(self):
    """Create customer management tab."""
    frame = ttk.Frame(self.notebook)
    self.notebook.add(frame, text="👥 Customers")

    # Search bar
    search_frame = ttk.Frame(frame)
    search_frame.pack(fill=tk.X, padx=5, pady=(5, 0))
    ttk.Label(search_frame, text="Search:").pack(side=tk.LEFT)
    self.customers_search_entry = ttk.Entry(search_frame, width=30)
    self.customers_search_entry.pack(side=tk.LEFT, padx=5)
    ttk.Button(
        search_frame, text="Search", command=self.search_customers_tab
    ).pack(side=tk.LEFT, padx=2)
    ttk.Button(
        search_frame, text="Clear", command=self.clear_customers_search
    ).pack(side=tk.LEFT, padx=2)

    # Customers table
    tree_frame = ttk.LabelFrame(frame, text="Registered Customers", padding=10)
    tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    # show="headings" hides the default tree column (#0) so the first data column aligns left.
    self.customers_tree = ttk.Treeview(
        tree_frame,
        columns=("ID", "Name", "Telephone", "Email", "Points", "Tier", "Spent"),
        height=15,
        show="headings",
    )
    self.customers_tree.column("ID", width=100)
    self.customers_tree.column("Name", width=130)
    self.customers_tree.column("Telephone", width=110)
    self.customers_tree.column("Email", width=150)
    self.customers_tree.column("Points", width=70)
    self.customers_tree.column("Tier", width=100)
    self.customers_tree.column("Spent", width=100)

    self.customers_tree.heading("ID", text="Customer ID")
    self.customers_tree.heading("Name", text="Name")
    self.customers_tree.heading("Telephone", text="Telephone")
    self.customers_tree.heading("Email", text="Email")
    self.customers_tree.heading("Points", text="Points")
    self.customers_tree.heading("Tier", text="Tier")
    self.customers_tree.heading("Spent", text="Total Spent")

    self.customers_tree.pack(fill=tk.BOTH, expand=True)
    self.customers_tree.bind("<Double-1>", lambda e: self.modify_customer())
    self._enable_tree_id_copy(
        self.customers_tree, id_col_index=0, label="Customer ID"
    )

    # Action buttons
    button_frame = ttk.Frame(frame)
    button_frame.pack(fill=tk.X, padx=5, pady=5)
    ttk.Button(
        button_frame, text="➕ Add New", command=self.add_new_customer
    ).pack(side=tk.LEFT, padx=5)
    ttk.Button(
        button_frame, text="✏️ Modify Selected", command=self.modify_customer
    ).pack(side=tk.LEFT, padx=5)
    ttk.Button(
        button_frame, text="🗑️ Delete Selected", command=self.delete_customer
    ).pack(side=tk.LEFT, padx=5)

    self.refresh_customers_display()


def search_customers_tab(self):
    self._customers_search_query = self.customers_search_entry.get()
    self.refresh_customers_display()


def clear_customers_search(self):
    self._customers_search_query = ""
    if hasattr(self, "customers_search_entry"):
        self.customers_search_entry.delete(0, tk.END)
    self.refresh_customers_display()


def add_new_customer(self):
    """Add new customer."""
    dialog = tk.Toplevel(self.root)
    dialog.title("Add New Customer")
    style_popup_window(dialog, self.root)
    dialog.geometry("440x200")
    dialog.columnconfigure(1, weight=1)

    ttk.Label(dialog, text="First Name:").grid(
        row=0, column=0, sticky="w", padx=10, pady=5
    )
    first_entry = ttk.Entry(dialog, width=25)
    first_entry.grid(row=0, column=1, sticky="ew", padx=10, pady=5)

    ttk.Label(dialog, text="Last Name:").grid(
        row=1, column=0, sticky="w", padx=10, pady=5
    )
    last_entry = ttk.Entry(dialog, width=25)
    last_entry.grid(row=1, column=1, sticky="ew", padx=10, pady=5)

    ttk.Label(dialog, text="Telephone:").grid(
        row=2, column=0, sticky="w", padx=10, pady=5
    )
    phone_entry = ttk.Entry(dialog, width=25)
    phone_entry.grid(row=2, column=1, sticky="ew", padx=10, pady=5)

    ttk.Label(dialog, text="Email:").grid(
        row=3, column=0, sticky="w", padx=10, pady=5
    )
    email_entry = ttk.Entry(dialog, width=25)
    email_entry.grid(row=3, column=1, sticky="ew", padx=10, pady=5)

    def save_customer():
        first_name = first_entry.get().strip()
        last_name = last_entry.get().strip()
        phone = phone_entry.get().strip()
        email = email_entry.get().strip()

        if not first_name and not last_name:
            messagebox.showerror(
                "Error", "Enter at least first name or last name"
            )
            return
        if not phone:
            messagebox.showerror("Error", "Telephone is required")
            return
        if not email:
            messagebox.showerror(
                "Error", "Email is required (for receipt delivery)"
            )
            return

        cid = utils.generate_customer_id()
        customer = Customer(first_name or " ", last_name or " ", cid, phone, email)
        self.store.add_customer(customer)
        self.data_manager.save_customers(self.store._customers)
        messagebox.showinfo("Success", f"Customer {cid} created")
        dialog.destroy()
        # Keep sales UI in sync (if currently displaying a customer)
        self._refresh_customer_display()
        self.refresh_customers_display()

    ttk.Button(
        dialog, text="Save", command=save_customer
    ).grid(row=4, column=0, columnspan=2, sticky="ew", padx=10, pady=10)
    center_toplevel(dialog, self.root)


def modify_customer(self):
    """Modify selected customer (name, telephone)."""
    selection = self.customers_tree.selection()
    if not selection:
        messagebox.showwarning(
            "Warning", "Please select a customer to modify"
        )
        return

    item = selection[0]
    values = self.customers_tree.item(item, "values")
    cust_id = str(values[0])
    cust = self.store.get_customer(cust_id)
    if not cust:
        messagebox.showerror("Error", "Customer not found")
        return

    dialog = tk.Toplevel(self.root)
    dialog.title("Modify Customer")
    dialog.geometry("380x200")
    dialog.transient(self.root)
    dialog.columnconfigure(1, weight=1)

    ttk.Label(dialog, text="Customer ID:").grid(
        row=0, column=0, sticky="w", padx=10, pady=5
    )
    id_entry = ttk.Entry(dialog, width=25)
    id_entry.insert(0, cust_id)
    id_entry.configure(state="readonly")
    id_entry.grid(row=0, column=1, sticky="ew", padx=10, pady=5)

    ttk.Label(dialog, text="First Name:").grid(
        row=1, column=0, sticky="w", padx=10, pady=5
    )
    first_entry = ttk.Entry(dialog, width=25)
    first_entry.insert(0, cust.first_name)
    first_entry.grid(row=1, column=1, padx=10, pady=5)

    ttk.Label(dialog, text="Last Name:").grid(
        row=2, column=0, sticky="w", padx=10, pady=5
    )
    last_entry = ttk.Entry(dialog, width=25)
    last_entry.insert(0, cust.last_name)
    last_entry.grid(row=2, column=1, padx=10, pady=5)

    ttk.Label(dialog, text="Telephone:").grid(
        row=3, column=0, sticky="w", padx=10, pady=5
    )
    phone_entry = ttk.Entry(dialog, width=25)
    phone_entry.insert(0, cust.telephone)
    phone_entry.grid(row=3, column=1, padx=10, pady=5)

    ttk.Label(dialog, text="Email:").grid(
        row=4, column=0, sticky="w", padx=10, pady=5
    )
    email_entry = ttk.Entry(dialog, width=25)
    email_entry.insert(0, cust.email)
    email_entry.grid(row=4, column=1, padx=10, pady=5)

    def save_changes():
        first_name = first_entry.get().strip()
        last_name = last_entry.get().strip()
        phone = phone_entry.get().strip()
        email = email_entry.get().strip()

        if not first_name and not last_name:
            messagebox.showerror(
                "Error", "Enter at least first name or last name"
            )
            return
        if not phone:
            messagebox.showerror("Error", "Telephone is required")
            return
        if not email:
            messagebox.showerror(
                "Error", "Email is required (for receipt delivery)"
            )
            return

        cust.update_info(
            first_name=first_name or " ",
            last_name=last_name or " ",
            telephone=phone,
            email=email,
        )
        self.data_manager.save_customers(self.store._customers)
        messagebox.showinfo("Success", "Customer updated")
        dialog.destroy()
        self._refresh_customer_display()
        self.refresh_customers_display()

    ttk.Button(
        dialog, text="Save", command=save_changes
    ).grid(row=5, column=0, columnspan=2, sticky="ew", padx=10, pady=10)
    center_toplevel(dialog, self.root)


def delete_customer(self):
    """Delete selected customer."""
    selection = self.customers_tree.selection()
    if not selection:
        messagebox.showwarning(
            "Warning", "Please select a customer to delete"
        )
        return

    item = selection[0]
    values = self.customers_tree.item(item, "values")
    cust_id = str(values[0])
    name = str(values[1])

    if not messagebox.askyesno(
        "Confirm Delete",
        f"Delete customer '{name}' ({cust_id})?\n\nThis cannot be undone.",
    ):
        return

    if self.store.delete_customer(cust_id):
        self.data_manager.save_customers(self.store._customers)
        messagebox.showinfo("Success", "Customer deleted")
        self._refresh_customer_display()
        self.refresh_customers_display()
    else:
        messagebox.showerror("Error", "Failed to delete customer")


def refresh_customers_display(self):
    """Refresh customers table."""
    for item in self.customers_tree.get_children():
        self.customers_tree.delete(item)

    query = getattr(self, "_customers_search_query", "").strip().lower()

    def _customer_id_sort_key(cust: Customer):
        cid = str(cust.person_id).strip().upper()
        if cid.startswith("CUS") and cid[3:].isdigit():
            return (0, int(cid[3:]))
        if cid.startswith("CUST") and cid[4:].isdigit():
            return (0, int(cid[4:]))
        return (1, cid)

    for cust in sorted(self.store._customers.values(), key=_customer_id_sort_key):
        if query:
            haystack = " ".join(
                [
                    cust.person_id,
                    cust.name,
                    cust.telephone,
                    cust.email,
                    cust.get_tier(),
                ]
            ).lower()
            if query not in haystack:
                continue

        self.customers_tree.insert(
            "",
            tk.END,
            values=(
                cust.person_id,
                cust.name,
                cust.telephone,
                cust.email,
                f"{cust.loyalty_points}",
                cust.get_tier(),
                f"HKD {cust.total_spent:.2f}",
            ),
        )

