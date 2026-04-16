"""
inventory.py - Inventory Management and ISBN Lookup Integration
"""

from models import Store, Book, NonBook


class InventoryManager:
    """Manage bookstore inventory."""

    def __init__(self, store: Store):
        """Initialize inventory manager."""
        self.store = store
        self.isbn_cache = {}

    def add_book_manual(
        self,
        name: str,
        isbn: str,
        author: str,
        price: float,
        stock: int,
        category: str = "General",
        subcategory: str = "",
        subtitle: str = "",
        publisher: str = "",
        publication_date: str = "",
        subject: str = "",
        cover_url: str = "",
    ) -> bool:
        """Add book manually without API lookup."""
        isbn = str(isbn).strip()
        if self.store.get_book(isbn):
            print(f"Error: ISBN {isbn} already exists")
            return False

        book = Book(name, price, isbn, author, category, subcategory)
        book.stock = stock
        book.subtitle = subtitle
        book.publisher = publisher
        book.publication_date = publication_date
        book.subject = subject or ""
        book.cover_url = (cover_url or "").strip()

        return self.store.add_book(book)

    def add_nonbook_manual(
        self,
        name: str,
        price: float,
        gtin: str,
        category: str,
        subcategory: str = "",
        stock: int = 0,
        brand: str = "",
        model: str = "",
    ) -> bool:
        """Add non-book product manually (GTIN = barcode for POS scanning)."""
        gtin = str(gtin).strip()
        if self.store.get_nonbook(gtin) or self.store.get_product(gtin):
            print(f"Error: GTIN {gtin} already exists")
            return False
        nb = NonBook(name, price, gtin, category, subcategory, brand, model)
        nb.stock = stock
        return self.store.add_product(nb)

    def delete_product(self, key: str) -> bool:
        """Delete any product (Book or Nonbook) by key (ISBN or GTIN)."""
        return self.store.delete_product(key)
