"""
main.py - Entry Point for Bookstore Management System
Hong Kong POS with ISBN Lookup and Barcode Scanning
"""

import tkinter as tk
import sys
from gui import BookstorePOS


if __name__ == "__main__":
    """
    Main entry point - follows Python conventions.
    
    OOP Concepts Demonstrated:
    ✓ Abstract Base Classes (Product, Person)
    ✓ Inheritance (Book→Product, Customer→Person)
    ✓ Encapsulation (private attributes with properties)
    ✓ Polymorphism (get_price(), is_available() overrides)
    ✓ Magic Methods (__init__, __str__, __eq__, __add__, __len__)
    ✓ Class Methods (@classmethod Book.from_isbn_data)
    ✓ Static Methods (@staticmethod generate_id, validate_isbn)
    ✓ Multiple Files (models, gui, sales, inventory, scanner, api, data)
    ✓ Random Numbers (uuid generation for IDs)
    ✓ API Integration (Google Books, Open Library)
    ✓ Barcode Scanning (OpenCV, pyzbar)
    ✓ JSON Persistence (data_manager)
    ✓ Tkinter GUI
    ✓ Hong Kong No-GST Compliant
    
    Features:
    - Inventory management with ISBN API lookup
    - POS sales with barcode scanning
    - Customer loyalty program (Bronze/Silver/Gold tiers)
    - Receipt generation (HKD, no tax)
    - JSON data persistence
    
    Usage:
        python main.py
    
    Requirements:
        pip install -r requirements.txt
    """
    
    try:
        root = tk.Tk()
        app = BookstorePOS(root)
        root.mainloop()
    
    except ImportError as e:
        print(f"Error: Missing required module: {e}")
        print("\nPlease install requirements:")
        print("  pip install -r requirements.txt")
        sys.exit(1)
    
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)
