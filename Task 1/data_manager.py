"""
JSON persistence for the bookstore app.

All paths default under data/ (inventory.json, customers.json, staff.json,
attendance.json, suppliers.json, purchase_orders.json, sales_history.json,
bookstore_profile.json). id_counters.json in the same folder holds sequential IDs (see utils.next_sequence).

Callers: BookstorePOS startup / save (via gui_pkg.app_lifecycle) and scattered GUI
handlers. Load_* builds dicts or model instances; save_* takes live Store fields
(or equivalent) and writes UTF-8 JSON.
"""

import json
import os
from typing import Dict, List, Any, Optional
from datetime import datetime
from models import Book, NonBook, Customer, Supplier, PurchaseOrder, Staff


class DataManager:
    """Read and write domain data as JSON files in self.data_dir (default data/)."""
    
    def __init__(self, data_dir: str = "data"):
        """Initialize data manager."""
        self.data_dir = data_dir
        self.inventory_file = os.path.join(data_dir, "inventory.json")
        self.customers_file = os.path.join(data_dir, "customers.json")
        self.suppliers_file = os.path.join(data_dir, "suppliers.json")
        self.purchase_orders_file = os.path.join(data_dir, "purchase_orders.json")
        self.sales_file = os.path.join(data_dir, "sales_history.json")
        self.bookstore_profile_file = os.path.join(data_dir, "bookstore_profile.json")
        self.staff_file = os.path.join(data_dir, "staff.json")
        self.attendance_file = os.path.join(data_dir, "attendance.json")
        
        self._ensure_data_dir()
    
    def _ensure_data_dir(self) -> None:
        """Ensure data directory exists."""
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
    
    def save_inventory(self, inventory: Dict[str, Any]) -> bool:
        """Save inventory (Book and Nonbook) to JSON. Values are Product instances."""
        try:
            data = []
            for p in inventory.values():
                d = p.to_dict()
                d['product_type'] = p.product_type_name()
                data.append(d)
            with open(self.inventory_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error saving inventory: {e}")
            return False
    
    def load_inventory(self) -> Dict[str, Any]:
        """Load inventory from JSON. Returns Dict[key, Product] (Book or Nonbook)."""
        if not os.path.exists(self.inventory_file):
            return {}
        
        try:
            with open(self.inventory_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            inventory = {}
            for item in data:
                pt = item.get('product_type', 'Book')
                if pt in ('NonBook', 'Nonbook'):
                    nb = NonBook(
                        name=item['name'],
                        price=float(item['price']),
                        gtin=item.get('gtin', item.get('sku', '')),
                        category=item['category'],
                        subcategory=item.get('subcategory', ''),
                        brand=item.get('brand', ''),
                        model=item.get('model', ''),
                    )
                    nb.stock = item.get('stock', 0)
                    nb.update_reorder_params(
                        minimum_stock_level=int(item.get('minimum_stock_level', 0) or 0),
                        maximum_stock_level=int(item.get('maximum_stock_level', 0) or 0),
                        lead_time_days=int(item.get('lead_time_days', 0) or 0),
                        average_daily_sales=float(item.get('average_daily_sales', 0.0) or 0.0),
                        default_supplier_id=str(item.get('default_supplier_id', '') or ''),
                        reorder_enabled=bool(item.get('reorder_enabled', False)),
                    )
                    nb.product_image = str(item.get('product_image', '') or '')
                    inventory[nb.gtin] = nb
                else:
                    book = Book(
                        name=item['name'],
                        price=float(item['price']),
                        isbn=item['isbn'],
                        author=item['author'],
                        category=item.get('category', 'General'),
                        subcategory=item.get('subcategory', '')
                    )
                    book.stock = item.get('stock', 0)
                    book.update_reorder_params(
                        minimum_stock_level=int(item.get('minimum_stock_level', 0) or 0),
                        maximum_stock_level=int(item.get('maximum_stock_level', 0) or 0),
                        lead_time_days=int(item.get('lead_time_days', 0) or 0),
                        average_daily_sales=float(item.get('average_daily_sales', 0.0) or 0.0),
                        default_supplier_id=str(item.get('default_supplier_id', '') or ''),
                        reorder_enabled=bool(item.get('reorder_enabled', False)),
                    )
                    book.publisher = item.get('publisher', '')
                    book.pages = item.get('pages', 0)
                    book.cover_url = item.get('cover_url', '')
                    book.subtitle = item.get('subtitle', '')
                    book.publication_date = item.get('publication_date', '')
                    book.subject = item.get('subject', '')
                    inventory[book.isbn] = book
            
            return inventory
        except Exception as e:
            print(f"Error loading inventory: {e}")
            return {}
    
    def save_customers(self, customers: Dict[str, Customer]) -> bool:
        """Save customers to JSON."""
        try:
            data = [cust.to_dict() for cust in customers.values()]
            with open(self.customers_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error saving customers: {e}")
            return False
    
    def load_customers(self) -> Dict[str, Customer]:
        """Load customers from JSON."""
        if not os.path.exists(self.customers_file):
            return {}
        
        try:
            with open(self.customers_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            customers = {}
            for item in data:
                if 'first_name' in item and 'last_name' in item:
                    first_name = item['first_name']
                    last_name = item['last_name']
                    telephone = item.get('telephone', '') or ''
                    email = item.get('email', '') or ''
                else:
                    name = item.get('name', ' ').strip()
                    parts = name.split(None, 1)
                    first_name = parts[0] if parts else ''
                    last_name = parts[1] if len(parts) > 1 else ''
                    telephone = item.get('telephone', '') or ''
                    email = item.get('email', '') or ''
                cust = Customer(first_name, last_name, item['customer_id'], telephone, email)
                cust._loyalty_points = item.get('loyalty_points', 0)
                cust._total_spent = item.get('total_spent', 0.0)
                cust._purchase_history = item.get('purchase_history', [])
                customers[cust.person_id] = cust
            
            return customers
        except Exception as e:
            print(f"Error loading customers: {e}")
            return {}
    
    def save_suppliers(self, suppliers: Dict[str, Supplier]) -> bool:
        """Save suppliers to JSON."""
        try:
            data = [supp.to_dict() for supp in suppliers.values()]
            with open(self.suppliers_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error saving suppliers: {e}")
            return False
    
    def load_suppliers(self) -> Dict[str, Supplier]:
        """Load suppliers from JSON."""
        if not os.path.exists(self.suppliers_file):
            return {}
        
        try:
            with open(self.suppliers_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            suppliers = {}
            for item in data:
                legacy_phone = item.get("phone") or item.get("contact", "")
                supp = Supplier(
                    item["name"],
                    item["supplier_id"],
                    contact_person=item.get("contact_person", ""),
                    address=item.get("address", ""),
                    phone=legacy_phone,
                    email=item.get("email", ""),
                )
                cat = item.get("supplied_catalog")
                if isinstance(cat, dict) and cat:
                    supp.set_catalog_prices({str(k): float(v) for k, v in cat.items()})
                else:
                    keys = item.get("supplied_product_keys")
                    if keys is None:
                        keys = item.get("supplied_books", [])
                    supp.set_catalog_keys(list(keys) if keys else [])
                suppliers[supp.person_id] = supp
            
            return suppliers
        except Exception as e:
            print(f"Error loading suppliers: {e}")
            return {}

    def save_purchase_orders(self, orders: Dict[str, PurchaseOrder]) -> bool:
        """Save purchase orders to JSON."""
        try:
            data = [po.to_dict() for po in orders.values()]
            with open(self.purchase_orders_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error saving purchase orders: {e}")
            return False

    def load_purchase_orders(self) -> Dict[str, PurchaseOrder]:
        """Load purchase orders from JSON."""
        if not os.path.exists(self.purchase_orders_file):
            return {}
        try:
            with open(self.purchase_orders_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            out: Dict[str, PurchaseOrder] = {}
            for item in data:
                po = PurchaseOrder.from_dict(item)
                out[po.po_id] = po
            return out
        except Exception as e:
            print(f"Error loading purchase orders: {e}")
            return {}

    def save_staff(self, staff: Dict[str, Staff]) -> bool:
        """Save staff directory."""
        try:
            data = [st.to_dict() for st in staff.values()]
            with open(self.staff_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error saving staff: {e}")
            return False

    def load_staff(self) -> Dict[str, Staff]:
        """Load staff directory."""
        if not os.path.exists(self.staff_file):
            return {}
        try:
            with open(self.staff_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            out: Dict[str, Staff] = {}
            for item in data:
                st = Staff.from_dict(item)
                if st.person_id:
                    out[st.person_id] = st
            return out
        except Exception as e:
            print(f"Error loading staff: {e}")
            return {}

    def save_attendance_records(self, records: List[Dict[str, Any]]) -> bool:
        """Save attendance records."""
        try:
            with open(self.attendance_file, "w", encoding="utf-8") as f:
                json.dump(records or [], f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error saving attendance: {e}")
            return False

    def load_attendance_records(self) -> List[Dict[str, Any]]:
        """Load attendance records."""
        if not os.path.exists(self.attendance_file):
            return []
        try:
            with open(self.attendance_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data if isinstance(data, list) else []
        except Exception as e:
            print(f"Error loading attendance: {e}")
            return []

    def append_sale(self, receipt_data: Dict[str, Any]) -> bool:
        """Append sale to history."""
        try:
            sales = []
            if os.path.exists(self.sales_file):
                with open(self.sales_file, 'r', encoding='utf-8') as f:
                    sales = json.load(f)
            
            sales.append(receipt_data)
            
            with open(self.sales_file, 'w', encoding='utf-8') as f:
                json.dump(sales, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error saving sale: {e}")
            return False

    def load_sales_history(self) -> List[Dict[str, Any]]:
        """Load sales history (previous transactions)."""
        if not os.path.exists(self.sales_file):
            return []
        try:
            with open(self.sales_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data if isinstance(data, list) else []
        except Exception as e:
            print(f"Error loading sales history: {e}")
            return []

    def save_bookstore_profile(self, profile: Dict[str, Any]) -> bool:
        """Save bookstore profile used on PO printout."""
        try:
            with open(self.bookstore_profile_file, "w", encoding="utf-8") as f:
                json.dump(profile or {}, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error saving bookstore profile: {e}")
            return False

    def load_bookstore_profile(self) -> Dict[str, Any]:
        """Load bookstore profile for PO letterhead."""
        if not os.path.exists(self.bookstore_profile_file):
            return {}
        try:
            with open(self.bookstore_profile_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data if isinstance(data, dict) else {}
        except Exception as e:
            print(f"Error loading bookstore profile: {e}")
            return {}
