"""
models.py - Core OOP Classes for Bookstore Management System
Demonstrates: Inheritance, Encapsulation, Polymorphism, Abstraction, Magic Methods
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime
import random
import json


class Person(ABC):
    """Abstract base class for people in system."""
    
    def __init__(self, name: str, person_id: str):
        """Initialize person with name and ID."""
        self._name = name
        self._person_id = person_id
    
    @property
    def name(self) -> str:
        """Get person's name (encapsulation)."""
        return self._name
    
    @property
    def person_id(self) -> str:
        """Get person's ID (encapsulation)."""
        return self._person_id
    
    @abstractmethod
    def get_details(self) -> str:
        """Abstract method - must implement in subclasses."""
        pass
    
    def __str__(self) -> str:
        """Magic method: string representation."""
        return f"{self.name} (ID: {self.person_id})"
    
    def __eq__(self, other) -> bool:
        """Magic method: equality comparison by ID."""
        if isinstance(other, Person):
            return self._person_id == other._person_id
        return False


class Product(ABC):
    """Abstract base class for sellable products."""
    
    def __init__(self, name: str, price: float):
        """Initialize product."""
        self.name = name
        self.price = price
        self._stock = 0
        self._created_date = datetime.now()
    
    @property
    def stock(self) -> int:
        """Get current stock (encapsulation)."""
        return self._stock
    
    @stock.setter
    def stock(self, value: int):
        """Set stock with validation."""
        if value < 0:
            raise ValueError("Stock cannot be negative")
        self._stock = value
    
    @abstractmethod
    def get_price(self) -> float:
        """Abstract method: get product price."""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Abstract method: check availability."""
        pass
    
    def update_stock(self, quantity: int) -> bool:
        """Update stock after sale."""
        if quantity > self._stock:
            return False
        self._stock -= quantity
        return True
    
    @staticmethod
    def generate_product_id() -> str:
        """Static method: generate random product ID."""
        return f"PROD{random.randint(10000, 99999)}"
    
    def __str__(self) -> str:
        """Magic method: string representation."""
        return f"{self.name} (HKD {self.price:.2f})"
    
    def __eq__(self, other) -> bool:
        """Magic method: equality by name (subclass override)."""
        if isinstance(other, Product):
            return self.name == other.name
        return False


class Book(Product):
    """Book subclass - inherits from Product."""
    
    def __init__(self, name: str, price: float, isbn: str, 
                 author: str, category: str = "General"):
        """Initialize book with OOP inheritance."""
        super().__init__(name, price)
        self.isbn = isbn
        self.author = author
        self.category = category
        self.cover_url = ""
        self.publisher = ""
        self.pages = 0
    
    def get_price(self) -> float:
        """Polymorphic implementation: get book price."""
        return self.price
    
    def is_available(self) -> bool:
        """Polymorphic implementation: check availability."""
        return self._stock > 0
    
    @classmethod
    def from_isbn_data(cls, data: Dict[str, Any], 
                       price: float, stock: int) -> 'Book':
        """Class method: create Book from API data."""
        book = cls(
            name=data.get('title', 'Unknown'),
            price=price,
            isbn=data.get('isbn', ''),
            author=data.get('authors', 'Unknown'),
            category=data.get('category', 'General')
        )
        book.stock = stock
        book.publisher = data.get('publisher', '')
        book.pages = data.get('pages', 0)
        book.cover_url = data.get('thumbnail', '')
        return book
    
    def __str__(self) -> str:
        """Magic method: detailed book representation."""
        return f"{self.name} by {self.author} (ISBN: {self.isbn})"
    
    def __eq__(self, other) -> bool:
        """Magic method: equality by ISBN."""
        if isinstance(other, Book):
            return self.isbn == other.isbn
        return False
    
    def __repr__(self) -> str:
        """Magic method: developer representation."""
        return f"Book(isbn='{self.isbn}', title='{self.name}', price={self.price})"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON persistence."""
        return {
            'name': self.name,
            'isbn': self.isbn,
            'author': self.author,
            'price': self.price,
            'stock': self.stock,
            'category': self.category,
            'publisher': self.publisher,
            'pages': self.pages,
            'cover_url': self.cover_url
        }


class Magazine(Product):
    """Magazine subclass - polymorphic variation of Product."""
    
    def __init__(self, name: str, price: float, issue_date: str):
        """Initialize magazine."""
        super().__init__(name, price)
        self.issue_date = issue_date
    
    def get_price(self) -> float:
        """Polymorphic: magazine pricing."""
        return self.price * 0.9  # 10% discount for magazines
    
    def is_available(self) -> bool:
        """Polymorphic: magazine availability."""
        return self._stock > 0


class Customer(Person):
    """Customer subclass with loyalty program."""
    
    def __init__(self, name: str, customer_id: str):
        """Initialize customer."""
        super().__init__(name, customer_id)
        self._loyalty_points = 0
        self._total_spent = 0.0
        self._purchase_history: List[Dict] = []
    
    @property
    def loyalty_points(self) -> int:
        """Get loyalty points (encapsulation)."""
        return self._loyalty_points
    
    @property
    def total_spent(self) -> float:
        """Get total amount spent."""
        return self._total_spent
    
    def get_details(self) -> str:
        """Polymorphic implementation: customer details."""
        tier = self.get_tier()
        return f"Customer: {self.name}, Tier: {tier}, Points: {self._loyalty_points}"
    
    def add_purchase(self, amount: float) -> None:
        """Add purchase and earn loyalty points."""
        # Calculate points: 1 point per HKD 10
        points = int(amount / 10)
        # Bonus: +50% for HKD 500+
        if amount >= 500:
            points = int(points * 1.5)
        
        self._loyalty_points += points
        self._total_spent += amount
        self._purchase_history.append({
            'date': datetime.now().isoformat(),
            'amount': amount,
            'points_earned': points
        })
    
    def get_discount_rate(self) -> float:
        """Get loyalty discount rate (0-15%)."""
        if self._loyalty_points >= 2000:
            return 0.15  # Gold tier
        elif self._loyalty_points >= 1000:
            return 0.10  # Silver tier
        elif self._loyalty_points >= 500:
            return 0.075  # Bronze tier
        return 0.0
    
    def get_tier(self) -> str:
        """Get customer loyalty tier."""
        if self._loyalty_points >= 2000:
            return "🥇 Gold"
        elif self._loyalty_points >= 1000:
            return "🥈 Silver"
        elif self._loyalty_points >= 500:
            return "🥉 Bronze"
        return "Standard"
    
    def __str__(self) -> str:
        """Magic method: customer string representation."""
        return f"{self.name} ({self.loyalty_points}pts - {self.get_tier()})"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for persistence."""
        return {
            'name': self._name,
            'customer_id': self._person_id,
            'loyalty_points': self._loyalty_points,
            'total_spent': self._total_spent,
            'purchase_history': self._purchase_history
        }


class Supplier(Person):
    """Supplier class for inventory sourcing."""
    
    def __init__(self, name: str, supplier_id: str, contact: str = ""):
        """Initialize supplier."""
        super().__init__(name, supplier_id)
        self.contact = contact
        self._supplied_books: List[str] = []  # ISBN list
    
    def get_details(self) -> str:
        """Polymorphic implementation: supplier details."""
        return f"Supplier: {self.name}, Contact: {self.contact}, Books: {len(self._supplied_books)}"
    
    def add_book(self, isbn: str) -> None:
        """Add book to supplier's catalog."""
        if isbn not in self._supplied_books:
            self._supplied_books.append(isbn)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for persistence."""
        return {
            'name': self._name,
            'supplier_id': self._person_id,
            'contact': self.contact,
            'supplied_books': self._supplied_books
        }


class OrderItem:
    """Represents an item in an order."""
    
    def __init__(self, book: Book, quantity: int):
        """Initialize order item."""
        self.book = book
        self.quantity = quantity
    
    def get_subtotal(self) -> float:
        """Calculate subtotal for this item."""
        return self.book.price * self.quantity
    
    def __str__(self) -> str:
        """String representation of order item."""
        return f"{self.book.name} ×{self.quantity} = HKD{self.get_subtotal():.2f}"


class Order:
    """Shopping cart and order management."""
    
    def __init__(self, order_id: str = ""):
        """Initialize order."""
        self.order_id = order_id or f"ORD{random.randint(100000, 999999)}"
        self._cart: List[OrderItem] = []
        self._created_date = datetime.now()
    
    def add_item(self, book: Book, quantity: int = 1) -> bool:
        """Add book to cart."""
        if not book.is_available() or quantity > book.stock:
            return False
        
        # Check if already in cart
        for item in self._cart:
            if item.book == book:
                item.quantity += quantity
                return True
        
        self._cart.append(OrderItem(book, quantity))
        return True
    
    def remove_item(self, isbn: str) -> bool:
        """Remove item by ISBN."""
        for i, item in enumerate(self._cart):
            if item.book.isbn == isbn:
                self._cart.pop(i)
                return True
        return False
    
    def get_items(self) -> List[OrderItem]:
        """Get all items in cart."""
        return self._cart
    
    @property
    def subtotal(self) -> float:
        """Calculate order subtotal."""
        return sum(item.get_subtotal() for item in self._cart)
    
    @property
    def total(self) -> float:
        """Get total (after discount, no tax in HK)."""
        return self.subtotal
    
    def __len__(self) -> int:
        """Magic method: number of items in cart."""
        return len(self._cart)
    
    def __str__(self) -> str:
        """Magic method: order representation."""
        return f"Order {self.order_id}: {len(self._cart)} items, HKD {self.total:.2f}"
    
    def __add__(self, book: Book) -> 'Order':
        """Magic method: add book to order with + operator."""
        self.add_item(book, 1)
        return self


class Receipt:
    """Receipt generation and formatting."""
    
    def __init__(self, order: Order, customer: Optional[Customer] = None, 
                 discount_amount: float = 0.0):
        """Initialize receipt."""
        self.receipt_id = f"RCP{random.randint(100000, 999999)}"
        self.order = order
        self.customer = customer
        self.discount_amount = discount_amount
        self.created_date = datetime.now()
    
    def calculate_final_total(self) -> float:
        """Calculate final total."""
        return self.order.subtotal - self.discount_amount
    
    def to_string(self) -> str:
        """Format receipt as string."""
        receipt_text = f"""
{'='*50}
ABC BOOKSTORE - RECEIPT
{'='*50}
Receipt ID: {self.receipt_id}
Date: {self.created_date.strftime('%Y-%m-%d %H:%M:%S')}
{'='*50}
"""
        
        if self.customer:
            receipt_text += f"Customer: {self.customer.name}\n"
            receipt_text += f"Loyalty Tier: {self.customer.get_tier()}\n"
        
        receipt_text += f"""{'='*50}
ITEMS:
"""
        for item in self.order.get_items():
            receipt_text += f"{item.book.name}\n"
            receipt_text += f"  {item.quantity} × HKD {item.book.price:.2f} = HKD {item.get_subtotal():.2f}\n"
        
        receipt_text += f"""{'='*50}
Subtotal:        HKD {self.order.subtotal:.2f}
"""
        
        if self.discount_amount > 0:
            rate = (self.discount_amount / self.order.subtotal) * 100
            receipt_text += f"Loyalty Discount: -HKD {self.discount_amount:.2f} ({rate:.1f}%)\n"
        
        receipt_text += f"""{'='*50}
TOTAL:           HKD {self.calculate_final_total():.2f}
{'='*50}
Thank you for shopping at ABC Bookstore!
No GST - Hong Kong
{'='*50}
"""
        return receipt_text
    
    def __str__(self) -> str:
        """String representation of receipt."""
        return self.to_string()


class Store:
    """Central store management system."""
    
    def __init__(self):
        """Initialize store."""
        self._inventory: Dict[str, Book] = {}
        self._customers: Dict[str, Customer] = {}
        self._suppliers: Dict[str, Supplier] = {}
        self._sales_history: List[Receipt] = []
    
    def add_book(self, book: Book) -> bool:
        """Add book to inventory."""
        if book.isbn in self._inventory:
            return False
        self._inventory[book.isbn] = book
        return True
    
    def get_book(self, isbn: str) -> Optional[Book]:
        """Get book by ISBN."""
        return self._inventory.get(isbn)
    
    def search_books(self, query: str, search_type: str = "title") -> List[Book]:
        """Search books by title/author/isbn."""
        results = []
        query_lower = query.lower()
        
        for book in self._inventory.values():
            if search_type == "title" and query_lower in book.name.lower():
                results.append(book)
            elif search_type == "author" and query_lower in book.author.lower():
                results.append(book)
            elif search_type == "isbn" and query == book.isbn:
                results.append(book)
        
        return results
    
    def add_customer(self, customer: Customer) -> bool:
        """Add customer to system."""
        if customer.person_id in self._customers:
            return False
        self._customers[customer.person_id] = customer
        return True
    
    def get_customer(self, customer_id: str) -> Optional[Customer]:
        """Get customer by ID."""
        return self._customers.get(customer_id)
    
    def get_all_customers(self) -> List[Customer]:
        """Get all customers."""
        return list(self._customers.values())
    
    def process_sale(self, order: Order, customer: Optional[Customer] = None) -> Optional[Receipt]:
        """Process a sale and update inventory."""
        # Calculate discount
        discount = 0.0
        if customer:
            discount = order.subtotal * customer.get_discount_rate()
        
        # Update inventory
        for item in order.get_items():
            if not item.book.update_stock(item.quantity):
                return None  # Out of stock
        
        # Update customer points
        final_total = order.subtotal - discount
        if customer:
            customer.add_purchase(final_total)
        
        # Create receipt
        receipt = Receipt(order, customer, discount)
        self._sales_history.append(receipt)
        
        return receipt
    
    def get_low_stock_books(self, threshold: int = 10) -> List[Book]:
        """Get books below stock threshold."""
        return [b for b in self._inventory.values() if b.stock < threshold]
    
    def get_sales_total(self, days: int = 1) -> float:
        """Get total sales for recent days."""
        cutoff = datetime.now().timestamp() - (days * 86400)
        total = 0.0
        for receipt in self._sales_history:
            if receipt.created_date.timestamp() > cutoff:
                total += receipt.calculate_final_total()
        return total
    
    def __len__(self) -> int:
        """Magic method: number of books in inventory."""
        return len(self._inventory)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert store state to dictionary."""
        return {
            'inventory': [b.to_dict() for b in self._inventory.values()],
            'customers': [c.to_dict() for c in self._customers.values()],
            'suppliers': [s.to_dict() for s in self._suppliers.values()]
        }
