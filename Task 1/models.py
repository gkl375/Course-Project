"""
models.py - Core OOP Classes for Bookstore Management System
Demonstrates: Inheritance, Encapsulation, Polymorphism, Abstraction, Magic Methods

Implementation is split under models_pkg/; this module re-exports the public API.
"""

from models_pkg.catalog import Product, Book, NonBook
from models_pkg.people import Person, Customer, Supplier, Staff
from models_pkg.orders import OrderItem, Order, Receipt, PurchaseOrderLine, PurchaseOrder
from models_pkg.store import Store
