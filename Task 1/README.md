# Bookstore Management System - User Guide

Tkinter desktop app for a small bookstore: **POS**, **inventory** (books + non-book items), **customers**, **staff & attendance**, **suppliers**, **purchase orders**, **reports**, and **JSON persistence**.

## Introduction video

https://github.com/user-attachments/assets/56513d4c-0c31-4438-aea0-f2aad3a189a2

---

## What it does

| Area | Behaviour |
|------|-----------|
| **Sales POS** | Cart by ISBN/GTIN; USB scanner into entry field; optional **continuous webcam** scan (`OpenCV` + `pyzbar`); customer loyalty discount at checkout; receipts update stock. |
| **Inventory** | Sub-tabs for **Book** (ISBN, API metadata, cover preview) and **Nonbook** (GTIN, categories, image). Reorder fields feed the Reports reorder reminder. |
| **Customers** | Loyalty points (1 point per HKD 10 spent); tier discounts: Standard 0%, Bronze (>=500 pts) 7.5%, Silver (>=1000 pts) 10%, Gold (>=2000 pts) 15%. |
| **Staff** | Staff records and same-day check-in / check-out; attendance stored in JSON. |
| **Suppliers & POs** | Supplier catalog keys and unit prices; create purchase orders and track status (Draft / Sent / Received / Cancelled). |
| **Reports** | Reorder reminder, summary stats, searchable transaction history. |
| **Settings** | Store profile and optional Google Books API key (`data/bookstore_profile.json`). |

---

## Project layout

```
Task 1/
├── main.py                 # Entry point (if __name__ == "__main__")
├── models.py               # Re-exports domain classes from models_pkg/
├── models_pkg/
│   ├── catalog.py          # Product(ABC), Book, NonBook
│   ├── people.py           # Person, Customer, Supplier, Staff
│   ├── orders.py           # Order, Receipt, PurchaseOrder, …
│   └── store.py            # Store aggregate (inventory, sales, POs, …)
├── gui.py                  # BookstorePOS shell; delegates to gui_pkg/
├── gui_pkg/                # One module per main notebook tab + helpers
├── sales.py                # SalesManager (cart, checkout)
├── inventory.py            # InventoryManager
├── data_manager.py         # Load/save JSON under data/
├── api_client.py           # ISBN lookup (Google Books, Open Library fallback)
├── scanner.py              # Barcode validation + continuous webcam scanning
├── utils.py                # Sequential IDs → data/id_counters.json, helpers
├── requirements.txt
├── data/                   # JSON persistence (see below)
└── README.md
```

**Sequential IDs:** receipt, customer, supplier, purchase order, and staff IDs are generated via `utils.next_sequence()` and stored in **`data/id_counters.json`** (not UUIDs).

---

## Object-oriented design

| Idea | Where |
|------|--------|
| **Abstract class** | `Product(ABC)` with abstract `get_product_key`, `get_price`, `is_available`, `product_type_name`. |
| **Inheritance** | `Book` / `NonBook` → `Product`; `Customer` / `Supplier` / `Staff` → `Person` (concrete base class). |
| **Polymorphism** | Same `Product` interface for books and non-book lines in cart and PO logic. |
| **Encapsulation** | Private-style fields (e.g. `_stock`, `_cart`) with properties / methods. |
| **Magic methods** | e.g. `Order.__add__` (used when adding **one** unit in `SalesManager.add_to_cart`), `__len__`, `__str__`, `__eq__`. |
| **Class / static methods** | e.g. `Receipt.from_saved_dict`, `PurchaseOrderLine.from_dict`, `Staff.from_dict`, scanner helpers. |
| **Class attributes** | e.g. `Book.BOOK_CATEGORIES`, `PurchaseOrder.VALID_STATUSES`. |

---

## Requirements

| Component | Notes |
|----------|------|
| Python 3.10+ | Recommended runtime for this project. |
| Tkinter | GUI dependency. |
| `requests` | HTTP client used by the API client (e.g., book lookups). |
| `opencv-python` | Webcam/barcode scanning support (OpenCV). |
| `numpy` | Numerical backend required by OpenCV. |
| `pyzbar` | Barcode reader (ZBar) support for scanned ISBN/GTIN. |
| `pillow` | Image processing for product images/covers. |

```bash
pip install -r requirements.txt
```

## Run

```bash
python main.py
```

Optional: set `GOOGLE_BOOKS_API_KEY` for higher Google Books quota (enter the key in **⚙️ Settings** in the app toolbar).

---

## Data files (`data/`)

| File | Role |
|------|------|
| `inventory.json` | Books and non-book products |
| `customers.json` | Customers, loyalty, telephone, email |
| `sales_history.json` | Receipts / transactions |
| `suppliers.json` | Suppliers and catalog prices |
| `purchase_orders.json` | PO headers and lines |
| `staff.json` | Staff directory |
| `attendance.json` | Check-in/out records |
| `bookstore_profile.json` | Store name, address, API key, etc. |
| `id_counters.json` | Next sequence numbers for generated IDs |

Data loads at startup and is saved after typical edits (checkout, dialogs, etc.).
