# ABC Bookstore Management System


## 📋 Overview

A complete point-of-sale (POS) system for Hong Kong bookstores featuring **ISBN API lookup**, **barcode scanning**, **loyalty discounts**, and **JSON persistence**. Demonstrates all OOP concepts across 9 modular Python files.

## ✨ Features

### 🛒 **POS Sales**
- **Barcode Scanning**: Webcam (OpenCV) or keyboard USB scanner support
- **ISBN Lookup**: Auto-fetch book details from Google Books/Open Library APIs
- **Shopping Cart**: Add/remove items, real-time total calculation
- **Loyalty Discounts**: Automatic tier-based discounts (Bronze/Silver/Gold)
- **Receipt Generation**: Professional HKD receipts (no GST)

### 📚 **Inventory Management**
- Add books with **ISBN API lookup** (auto-fill details)
- Manual add for custom entries
- Search by title/author/ISBN
- Low stock alerts (<10 units)
- Stock tracking per book

### 👥 **Customer Management**
- **Loyalty Program**:
  - 1 point per HKD 10 spent
  - +50% bonus for HKD 500+ purchases
  - Bronze (500+): 7.5% discount
  - Silver (1000+): 10% discount
  - Gold (2000+): 15% discount
- Customer registration & purchase history

### 📊 **Reporting**
- Daily/weekly sales summaries
- Low stock reports
- Customer leaderboard
- Inventory valuation

## 🏗️ OOP Architecture

### Class Hierarchy
```
Product (ABC)
├── Book (ISBN, author, API integration)
└── Magazine (issue_date)

Person (ABC)
├── Customer (loyalty_points, tiers)
└── Supplier (supplied_books)

Store (Central manager)
├── Order (shopping cart)
└── Receipt (HKD formatted)

Managers
├── SalesManager (POS logic)
├── InventoryManager (book CRUD + ISBN lookup)
└── DataManager (JSON persistence)

APIs
├── ISBNLookup (Google Books, Open Library)
└── BarcodeScanner (OpenCV, pyzbar, keyboard)
```

### OOP Concepts Implemented

| Concept | Implementation | File |
|---------|----------------|------|
| **Abstract Classes** | `Product(ABC)`, `Person(ABC)` | models.py |
| **Inheritance** | Book→Product, Customer→Person | models.py |
| **Encapsulation** | `@property`, private `_stock`, `_points` | models.py |
| **Polymorphism** | `get_price()`, `is_available()` overrides | models.py |
| **Magic Methods** | `__init__`, `__str__`, `__eq__`, `__add__`, `__len__` | models.py |
| **Class Methods** | `@classmethod Book.from_isbn_data()` | models.py |
| **Static Methods** | `@staticmethod generate_id()`, `validate_isbn()` | models.py, utils.py |
| **Modular Design** | 9 separate files, clear responsibilities | All |
| **Random Numbers** | ID generation with `random` module | utils.py |
| **Type Hints** | Full type annotations | All |

## 📁 File Structure

```
bookstore_system/
├── main.py                 # Entry point (if __name__ == '__main__')
├── models.py              # OOP classes (Product, Book, Customer, Store, Order, Receipt)
├── gui.py                 # Tkinter interface (1200x700, 5 tabs)
├── sales.py               # POS operations (cart, checkout, loyalty calc)
├── inventory.py           # Book management (CRUD, ISBN API)
├── scanner.py             # Barcode scanning (webcam/keyboard/manual)
├── api_client.py          # ISBN APIs (Google Books, Open Library)
├── data_manager.py        # JSON persistence (load/save)
├── utils.py               # Utilities (random IDs, validation, formatting)
├── requirements.txt       # Python dependencies
├── data/                  # JSON storage (auto-created)
│   ├── inventory.json
│   ├── customers.json
│   ├── suppliers.json
│   ├── sales_history.json
│   └── isbn_cache.json
└── README.md              # This file
```

## 🚀 Installation & Setup

### 1. Install Python 3.8+
```bash
python --version
```

### 2. Clone/Create Project
```bash
mkdir bookstore_system
cd bookstore_system
# Copy all .py files into this directory
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

**On Linux/Mac (for OpenCV barcode scanning):**
```bash
sudo apt-get install libzbar0          # Debian/Ubuntu
brew install zbar                       # macOS
```

### 4. Run Application
```bash
python main.py
```

✅ GUI window opens with 5 tabs

## 📖 Usage Guide

### 🛒 Sales POS Tab

**Workflow:**
1. Enter ISBN or click **📷 Scan** to capture barcode
2. Enter quantity (default 1)
3. Click **➕ Add to Cart**
4. Select customer (or add new)
5. View discount automatically applied
6. Click **✓ Checkout** to generate receipt
7. Receipt prints and stock updates

### 📚 Inventory Tab

**Add Book with ISBN Lookup:**
1. Enter ISBN-13 code
2. Click **🔍 Fetch Details** (auto-populates from API)
3. Override price & stock if needed
4. Click **✓ Add Book**

**Manual Add:**
1. Skip ISBN lookup
2. Fill Title, Author, Price, Stock
3. Click **✓ Add Book**

### 👥 Customers Tab

- View all registered customers
- Track loyalty points and tier
- See total spent per customer

### 📊 Reports Tab

- **Low Stock Alert**: Books below 10 units
- **Sales Summary**: Daily/weekly totals
- **Customer Stats**: Top spenders, total customers

## 🎯 Key OOP Demonstrations

### 1. Abstract Base Class
```python
class Product(ABC):
    @abstractmethod
    def get_price(self) -> float:
        pass

class Book(Product):
    def get_price(self) -> float:
        return self.price  # Polymorphic override
```

### 2. Encapsulation
```python
class Customer(Person):
    @property
    def loyalty_points(self) -> int:
        return self._loyalty_points  # Private with getter
    
    def add_purchase(self, amount: float):
        points = int(amount / 10)
        self._loyalty_points += points  # Controlled update
```

### 3. Inheritance & Polymorphism
```python
class Person(ABC):
    def __str__(self):
        return f"{self.name} (ID: {self.person_id})"

class Customer(Person):
    def __str__(self):
        return f"{self.name} ({self.loyalty_points}pts - {self.get_tier()})"
```

### 4. Magic Methods
```python
class Order:
    def __add__(self, book: Book) -> 'Order':
        self.add_item(book, 1)
        return self
    
    def __len__(self) -> int:
        return len(self._cart)
    
    def __str__(self) -> str:
        return f"Order {self.order_id}: {len(self)} items"
```

### 5. Class Methods & Static Methods
```python
class Book(Product):
    @classmethod
    def from_isbn_data(cls, data: Dict, price: float, stock: int) -> 'Book':
        book = cls(data['title'], price, data['isbn'], data['authors'])
        book.stock = stock
        return book
    
    @staticmethod
    def generate_product_id() -> str:
        return f"PROD{random.randint(10000, 99999)}"
```

## 💾 Data Persistence

### JSON Format
All data stored in `data/` directory (auto-created):

**inventory.json:**
```json
[
  {
    "name": "Clean Code",
    "isbn": "9780132350884",
    "author": "Robert C. Martin",
    "price": 49.99,
    "stock": 25,
    "category": "Tech",
    "publisher": "Prentice Hall"
  }
]
```

**customers.json:**
```json
[
  {
    "name": "John Doe",
    "customer_id": "CUST12345",
    "loyalty_points": 1250,
    "total_spent": 12500.50
  }
]
```

### Auto-Save
- Data loads on startup
- Save button in toolbar (💾 Save)
- Manual backup via file menu

## 🌐 ISBN API Integration

### Google Books API
- Free, no key required
- Primary source
- Returns: title, authors, publisher, category, description, thumbnail

### Open Library API
- Free, no key required
- Fallback if Google fails
- Same data fields

### Caching
- Offline lookups stored in `isbn_cache.json`
- Reduces API calls
- Network timeout gracefully falls back to manual entry

## 📱 Barcode Scanning

### 3 Input Methods
1. **Webcam** (OpenCV): Real-time video, detects EAN-13 barcodes
2. **USB Scanner**: Emulates keyboard, reads 13-digit codes
3. **Manual Entry**: Type ISBN directly

### Keyboard Shortcut (Scanning Tab)
- Press 'q': Quit scanning
- ESC: Abort
- Auto-timeout: 30 seconds

## 💰 Loyalty System

### Points Calculation
```
Base: 1 point per HKD 10
Example: HKD 250 → 25 points

Bonus: +50% for HKD 500+ purchases
Example: HKD 750 → 75 × 1.5 = 112.5 → 112 points
```

### Discount Tiers
```
🥉 Bronze:  500+ points  → 7.5% discount
🥈 Silver:  1000+ points → 10% discount
🥇 Gold:    2000+ points → 15% discount
```

### Example Receipt
```
Subtotal: HKD 897.00
Loyalty Discount (7.5%): -HKD 67.28
=====================================
TOTAL: HKD 829.72
```


## 🧪 Testing

### Sample Data
Run with sample inventory to test:

```python
# In main.py - add before root.mainloop()
def load_sample_data(app):
    from models import Book
    
    books = [
        ("Clean Code", "9780132350884", "Robert C. Martin", 49.99),
        ("Design Patterns", "9780201633610", "Gang of Four", 54.99),
        ("Python Cookbook", "9781491946269", "David Beazley", 39.99),
    ]
    
    for title, isbn, author, price in books:
        book = Book(title, price, isbn, author, "Tech")
        book.stock = random.randint(5, 30)
        app.store.add_book(book)
```

### Test Cases
- ✅ Add book with ISBN lookup
- ✅ Scan barcode (webcam/keyboard)
- ✅ Add to cart, apply loyalty
- ✅ Checkout, verify stock update
- ✅ Save/load data persistence
- ✅ Low stock alert
- ✅ Customer tier calculation

## ⚠️ Error Handling

- **No API response**: Falls back to manual entry
- **Invalid ISBN**: Validation prevents invalid codes
- **Out of stock**: Cart check prevents overselling
- **No webcam**: Uses keyboard/manual input
- **Missing data file**: Creates new file on startup
- **Network timeout**: 5-second timeout with fallback

## 📊 Performance

- **Inventory**: O(1) lookup by ISBN
- **Search**: O(n) linear search (acceptable for <1000 books)
- **API Calls**: Rate-limited with 0.5s delay
- **UI Refresh**: Efficient tree updates
- **JSON I/O**: Lazy load/save pattern





---

**Ready to run:** `python main.py`

Enjoy your OOP Bookstore Management System! 📚🛒
