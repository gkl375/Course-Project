"""
main.py - Entry Point for Bookstore Management System
Hong Kong POS with ISBN Lookup and Barcode Scanning
"""

import tkinter as tk
import sys
import os
from gui import BookstorePOS
from api_client import ISBNLookup


if __name__ == "__main__":
    """
    Main entry point - follows Python conventions.

    Object-oriented structure (summary):
    ✓ Abstract Base Classes (Product)
    ✓ Inheritance (Book→Product, Customer→Person)
    ✓ Encapsulation (private attributes with properties)
    ✓ Polymorphism (get_price(), is_available() overrides)
    ✓ Magic Methods (__init__, __str__, __eq__, __add__, __len__)
    ✓ Class / static methods (e.g. Staff.from_dict, BarcodeScanner helpers, utils id generators)
    ✓ Multiple Files (models, gui, sales, inventory, scanner, api, data)
    ✓ Sequential IDs (persisted in data/id_counters.json)
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
        # Initialize Google Books API key (if available)
        # Get from environment variable or config
        google_api_key = os.getenv('GOOGLE_BOOKS_API_KEY')
        if google_api_key:
            ISBNLookup.set_api_key(google_api_key)
            print(f"✓ Google Books API key loaded (1M queries/day quota)")
        else:
            # Keep startup logs ASCII-only for Windows console compatibility (cp950/cp1252).
            print("[!] No Google Books API key set - using unauthenticated mode (100 queries/day)")
            print("    To enable full quota: set GOOGLE_BOOKS_API_KEY environment variable")
            print("    Get free API key at: https://console.cloud.google.com/apis/library/books.googleapis.com")
        
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
