"""
Domain model package (bookstore entities).

- catalog: Product ABC, Book, NonBook
- people: Person, Customer, Supplier, Staff
- orders: OrderItem, Order, Receipt, PurchaseOrder, PurchaseOrderLine
- store: Store — in-memory aggregate used by the GUI and managers; filled and flushed via DataManager + JSON in data/

Public imports for the rest of the app are re-exported from the parent models.py module.
"""
