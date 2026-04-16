"""
Store aggregate: single in-memory hub for inventory, customers, staff, attendance,
suppliers, purchase orders, sales history, and bookstore profile fields.

The GUI and SalesManager/InventoryManager read and mutate this object. Persistence is
not done here: DataManager loads JSON from data/ into these dicts/lists at startup
and writes them back on save, checkout, and similar actions.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from models import Book, Customer, NonBook, Order, PurchaseOrder, PurchaseOrderLine, Receipt, Staff, Supplier


class Store:
    """Central store management system. Inventory holds both Book and Nonbook (Product)."""

    def __init__(self):
        """Initialize store."""
        self._inventory: Dict[str, "Product"] = {}
        self._customers: Dict[str, Customer] = {}
        self._suppliers: Dict[str, Supplier] = {}
        self._staff: Dict[str, Staff] = {}
        self._attendance_records: List[Dict[str, Any]] = []
        self._purchase_orders: Dict[str, PurchaseOrder] = {}
        self._sales_history: List[Receipt] = []
        # Printed on purchase orders (edit via Settings / bookstore_profile.json)
        self.bookstore_name: str = "ABC Bookstore"
        self.bookstore_address: str = ""
        self.bookstore_contact_name: str = ""
        self.bookstore_phone: str = ""
        self.bookstore_email: str = ""
        self.google_books_api_key: str = ""

    def apply_bookstore_profile(self, d: Dict[str, Any]) -> None:
        """Load bookstore letterhead fields from dict (e.g. JSON)."""
        if not d:
            return
        self.bookstore_name = str(d.get("bookstore_name", self.bookstore_name) or "").strip() or self.bookstore_name
        self.bookstore_address = str(d.get("bookstore_address", "") or "").strip()
        self.bookstore_contact_name = str(d.get("bookstore_contact_name", "") or "").strip()
        self.bookstore_phone = str(d.get("bookstore_phone", "") or "").strip()
        self.bookstore_email = str(d.get("bookstore_email", "") or "").strip()
        self.google_books_api_key = str(d.get("google_books_api_key", "") or "").strip()

    def bookstore_profile_dict(self) -> Dict[str, Any]:
        """Serialize bookstore letterhead for persistence."""
        return {
            "bookstore_name": self.bookstore_name,
            "bookstore_address": self.bookstore_address,
            "bookstore_contact_name": self.bookstore_contact_name,
            "bookstore_phone": self.bookstore_phone,
            "bookstore_email": self.bookstore_email,
            "google_books_api_key": self.google_books_api_key,
        }

    def add_product(self, product: "Product") -> bool:
        """Add any product (Book or Nonbook) to inventory. Key = get_product_key()."""
        key = product.get_product_key()
        if key in self._inventory:
            return False
        self._inventory[key] = product
        return True

    def get_product(self, key: str) -> Optional["Product"]:
        """Get product by key (ISBN for Book, GTIN for Nonbook)."""
        key = str(key).strip()
        if key in self._inventory:
            return self._inventory[key]
        if key.isdigit() and int(key) in self._inventory:
            return self._inventory[int(key)]  # type: ignore[index]
        return None

    def add_book(self, book: Book) -> bool:
        """Add book to inventory (delegates to add_product)."""
        isbn_key = str(book.isbn).strip()
        book.isbn = isbn_key
        return self.add_product(book)

    def get_book(self, isbn: str) -> Optional[Book]:
        """Get book by ISBN (returns None if key exists but is Nonbook)."""
        p = self.get_product(isbn)
        return p if isinstance(p, Book) else None

    def get_nonbook(self, gtin: str) -> Optional["NonBook"]:
        """Get non-book product by GTIN."""
        p = self.get_product(gtin)
        return p if isinstance(p, NonBook) else None

    def get_all_products(self) -> List["Product"]:
        """Get all products (Book and Nonbook) for display."""
        return list(self._inventory.values())

    def get_reorder_products(self) -> List["Product"]:
        """Products at/below reorder level (with reorder controls configured)."""
        out: List["Product"] = []
        for p in self._inventory.values():
            if not bool(getattr(p, "reorder_enabled", False)):
                continue
            if p.minimum_stock_level <= 0 and p.lead_time_days <= 0 and p.average_daily_sales <= 0:
                continue
            if p.stock <= p.reorder_level():
                out.append(p)
        return sorted(out, key=lambda x: (x.stock - x.reorder_level(), x.name))

    def find_open_po_for_product(self, product_key: str) -> Optional[PurchaseOrder]:
        key = str(product_key).strip()
        hits: List[PurchaseOrder] = []
        for po in self._purchase_orders.values():
            if po.status not in ("Draft", "Sent"):
                continue
            for ln in po.lines:
                if str(ln.product_key).strip() == key:
                    hits.append(po)
                    break
        if not hits:
            return None
        # Prefer Draft over Sent; then newest first.
        prio = {"Draft": 0, "Sent": 1}
        hits.sort(
            key=lambda p: (
                prio.get(p.status, 9),
                -float(getattr(p.created, "timestamp", lambda: 0.0)()),
            )
        )
        return hits[0]

    def find_related_po_for_reorder_display(self, product_key: str) -> Optional[PurchaseOrder]:
        """PO to show in reorder reminder: prefer Draft/Sent, else newest PO (any status) containing the key."""
        open_po = self.find_open_po_for_product(product_key)
        if open_po is not None:
            return open_po
        key = str(product_key).strip()
        hits: List[PurchaseOrder] = []
        for po in self._purchase_orders.values():
            for ln in po.lines:
                if str(ln.product_key).strip() == key:
                    hits.append(po)
                    break
        if not hits:
            return None
        hits.sort(key=lambda p: -float(getattr(p.created, "timestamp", lambda: 0.0)()))
        return hits[0]

    def auto_draft_reorder_purchase_orders(self) -> List[PurchaseOrder]:
        """Auto-create/extend draft POs for reorder products (if default supplier is set).

        Line quantity (Inventory requires maximum_stock_level > 0 when reorder is enabled):
            qty = maximum_stock_level - minimum_stock_level

        Rule:
        - If a Draft PO already exists for the same supplier, append new products to it.
        - Never modify Sent/Received/Cancelled POs.
        - Avoid adding the same product twice to any open PO (Draft/Sent).
        - Process reorder products in ISBN / GTIN string order so new lines follow that order.
        """
        created_or_updated: List[PurchaseOrder] = []

        def _auto_po_note_line(
            prefix: str, product_key: str, qty: int, reorder_lvl: int, stock: int
        ) -> str:
            return (
                f"{prefix}: {product_key} - qty={qty} (max-min), "
                f"reorder lvl={reorder_lvl}, stock={stock}"
            )

        def _get_supplier_draft_po(supplier_id: str) -> Optional[PurchaseOrder]:
            hits = [po for po in self._purchase_orders.values() if po.supplier_id == supplier_id and po.status == "Draft"]
            if not hits:
                return None
            hits.sort(key=lambda p: float(getattr(p.created, "timestamp", lambda: 0.0)()), reverse=True)
            return hits[0]

        reorder_sorted = sorted(
            self.get_reorder_products(),
            key=lambda x: str(x.get_product_key()).strip(),
        )
        for p in reorder_sorted:
            sid = str(getattr(p, "default_supplier_id", "") or "").strip()
            if not sid or self.get_supplier(sid) is None:
                continue

            key = str(p.get_product_key()).strip()
            if self.find_open_po_for_product(key) is not None:
                continue

            max_level = int(getattr(p, "maximum_stock_level", 0) or 0)
            min_level = int(getattr(p, "minimum_stock_level", 0) or 0)
            if max_level <= 0:
                continue
            qty = max_level - min_level
            if qty <= 0:
                continue
            stock_i = int(p.stock)
            reorder_level = p.reorder_level()
            sup = self.get_supplier(sid)
            unit = (
                sup.get_catalog_unit_price(key, float(p.price))
                if sup is not None
                else float(p.price)
            )

            po = _get_supplier_draft_po(sid)
            if po is None:
                po = PurchaseOrder(
                    sid,
                    lines=[PurchaseOrderLine(key, qty, unit)],
                    notes=_auto_po_note_line(
                        "Auto add", key, qty, reorder_level, stock_i
                    ),
                    status="Draft",
                )
                if self.add_purchase_order(po):
                    created_or_updated.append(po)
                continue

            # Append to existing supplier Draft PO
            po.lines.append(PurchaseOrderLine(key, qty, unit))
            add_line = _auto_po_note_line("Auto add", key, qty, reorder_level, stock_i)
            if po.notes:
                po.notes = po.notes + "\n" + add_line
            else:
                po.notes = add_line
            created_or_updated.append(po)

        return created_or_updated

    def delete_product(self, key: str) -> bool:
        """Remove product from inventory by key (ISBN or GTIN)."""
        key = str(key).strip()
        if key in self._inventory:
            del self._inventory[key]
            return True
        if key.isdigit():
            k = int(key)
            if k in self._inventory:
                del self._inventory[k]
                return True
        return False

    def add_customer(self, customer: Customer) -> bool:
        """Add customer to system."""
        if customer.person_id in self._customers:
            return False
        self._customers[customer.person_id] = customer
        return True

    def get_customer(self, customer_id: str) -> Optional[Customer]:
        """Get customer by ID."""
        return self._customers.get(customer_id)

    def delete_customer(self, customer_id: str) -> bool:
        """Remove customer from system. Returns True if deleted."""
        if customer_id in self._customers:
            del self._customers[customer_id]
            return True
        return False

    def set_staff(self, staff: Dict[str, Staff]) -> None:
        """Replace staff registry (e.g. after loading from JSON)."""
        self._staff.clear()
        self._staff.update(staff)

    def add_staff(self, staff: Staff) -> bool:
        """Add staff. Returns False if ID already exists."""
        sid = str(staff.person_id).strip()
        if not sid or sid in self._staff:
            return False
        self._staff[sid] = staff
        return True

    def get_staff(self, staff_id: str) -> Optional[Staff]:
        return self._staff.get(str(staff_id).strip())

    def delete_staff(self, staff_id: str) -> bool:
        sid = str(staff_id).strip()
        if sid in self._staff:
            del self._staff[sid]
            self._attendance_records = [
                r for r in self._attendance_records if str(r.get("staff_id", "")).strip() != sid
            ]
            return True
        return False

    def get_all_staff(self) -> List[Staff]:
        def _staff_sort_key(st: Staff) -> tuple:
            sid = str(st.person_id).strip().upper()
            if sid.startswith("STF") and sid[3:].isdigit():
                return (0, int(sid[3:]))
            return (1, sid.lower())

        return sorted(self._staff.values(), key=_staff_sort_key)

    def set_attendance_records(self, records: List[Dict[str, Any]]) -> None:
        clean: List[Dict[str, Any]] = []
        for r in records or []:
            sid = str(r.get("staff_id", "")).strip()
            d = str(r.get("date", "")).strip()
            if not sid or not d:
                continue
            clean.append(
                {
                    "staff_id": sid,
                    "date": d,
                    "check_in": str(r.get("check_in", "")).strip(),
                    "check_out": str(r.get("check_out", "")).strip(),
                }
            )
        self._attendance_records = clean

    def get_attendance_records(
        self,
        date_str: str = "",
        staff_id: str = "",
        date_from: str = "",
        date_to: str = "",
    ) -> List[Dict[str, Any]]:
        """Filter attendance. If date_str is set, match that day only (legacy). Otherwise use inclusive date_from/date_to (YYYY-MM-DD strings compare safely)."""
        d = (date_str or "").strip()
        sid = (staff_id or "").strip()
        df = (date_from or "").strip()
        dt = (date_to or "").strip()
        out: List[Dict[str, Any]] = []
        for r in self._attendance_records:
            rsid = str(r.get("staff_id", "")).strip()
            if sid and rsid != sid:
                continue
            rd = str(r.get("date", "")).strip()
            if d:
                if rd != d:
                    continue
            else:
                if df and rd < df:
                    continue
                if dt and rd > dt:
                    continue
            out.append(dict(r))
        return out

    def get_staff_attendance_for_date(self, staff_id: str, date_str: str) -> Dict[str, str]:
        sid = str(staff_id).strip()
        d = str(date_str).strip()
        check_in = ""
        check_out = ""
        for r in self._attendance_records:
            if str(r.get("staff_id", "")).strip() != sid:
                continue
            if str(r.get("date", "")).strip() != d:
                continue
            if str(r.get("check_in", "")).strip():
                check_in = str(r.get("check_in", "")).strip()
            if str(r.get("check_out", "")).strip():
                check_out = str(r.get("check_out", "")).strip()
        status = "Not checked in"
        if check_in and not check_out:
            status = "Checked in"
        elif check_in and check_out:
            status = "Checked out"
        return {"check_in": check_in, "check_out": check_out, "status": status}

    def check_in_staff(self, staff_id: str, at: Optional[datetime] = None) -> bool:
        sid = str(staff_id).strip()
        if sid not in self._staff:
            return False
        now = at or datetime.now()
        d = now.strftime("%Y-%m-%d")
        t = now.strftime("%H:%M:%S")
        today = self.get_staff_attendance_for_date(sid, d)
        if today["check_in"] and not today["check_out"]:
            return False
        self._attendance_records.append(
            {"staff_id": sid, "date": d, "check_in": t, "check_out": ""}
        )
        return True

    def check_out_staff(self, staff_id: str, at: Optional[datetime] = None) -> bool:
        sid = str(staff_id).strip()
        if sid not in self._staff:
            return False
        now = at or datetime.now()
        d = now.strftime("%Y-%m-%d")
        t = now.strftime("%H:%M:%S")
        for i in range(len(self._attendance_records) - 1, -1, -1):
            r = self._attendance_records[i]
            if str(r.get("staff_id", "")).strip() != sid:
                continue
            if str(r.get("date", "")).strip() != d:
                continue
            if not str(r.get("check_in", "")).strip():
                continue
            if str(r.get("check_out", "")).strip():
                continue
            r["check_out"] = t
            return True
        return False

    def set_suppliers(self, suppliers: Dict[str, Supplier]) -> None:
        """Replace supplier registry (e.g. after loading from JSON)."""
        self._suppliers.clear()
        self._suppliers.update(suppliers)

    def add_supplier(self, supplier: Supplier) -> bool:
        """Add supplier. Returns False if ID already exists."""
        if supplier.person_id in self._suppliers:
            return False
        self._suppliers[supplier.person_id] = supplier
        return True

    def get_supplier(self, supplier_id: str) -> Optional[Supplier]:
        """Get supplier by ID."""
        return self._suppliers.get(supplier_id)

    def delete_supplier(self, supplier_id: str) -> bool:
        """Remove supplier. Returns True if removed."""
        if supplier_id in self._suppliers:
            del self._suppliers[supplier_id]
            return True
        return False

    def get_all_suppliers(self) -> List[Supplier]:
        """Get all suppliers."""
        return list(self._suppliers.values())

    def set_purchase_orders(self, orders: Dict[str, PurchaseOrder]) -> None:
        """Replace purchase order registry (e.g. after loading from JSON)."""
        self._purchase_orders.clear()
        self._purchase_orders.update(orders)

    def add_purchase_order(self, po: PurchaseOrder) -> bool:
        """Add a purchase order. Returns False if PO id already exists."""
        if po.po_id in self._purchase_orders:
            return False
        self._purchase_orders[po.po_id] = po
        return True

    def get_purchase_order(self, po_id: str) -> Optional[PurchaseOrder]:
        return self._purchase_orders.get(po_id)

    def delete_purchase_order(self, po_id: str) -> bool:
        if po_id in self._purchase_orders:
            del self._purchase_orders[po_id]
            return True
        return False

    def get_all_purchase_orders(self) -> List[PurchaseOrder]:
        """Newest first."""
        return sorted(
            self._purchase_orders.values(),
            key=lambda p: p.created.timestamp(),
            reverse=True,
        )

    def process_sale(self, order: Order, customer: Optional[Customer] = None) -> Optional[Receipt]:
        """Process a sale and update inventory."""
        # Calculate discount
        discount = 0.0
        if customer:
            discount = order.subtotal * customer.get_discount_rate()

        # Update inventory
        for item in order.get_items():
            if not item.product.update_stock(item.quantity):
                return None  # Out of stock

        # Update customer points
        final_total: float = order.subtotal - discount
        cust = customer
        if cust is not None:
            cust.add_purchase(final_total)

        # Create receipt
        receipt = Receipt(order, customer, discount)
        receipt.store_name = (self.bookstore_name or "").strip() or "ABC Bookstore"
        self._sales_history.append(receipt)

        return receipt

    def load_sales_history_from_disk(self, data_manager: Any) -> None:
        """Rebuild ``_sales_history`` from ``sales_history.json``.

        Call after inventory and customers are loaded so :meth:`Receipt.from_saved_dict` can resolve products.
        """
        rows = data_manager.load_sales_history()
        loaded: List[Receipt] = []
        for row in rows:
            if not isinstance(row, dict):
                continue
            try:
                loaded.append(Receipt.from_saved_dict(row, self))
            except Exception:
                continue
        self._sales_history = loaded

    def get_sales_total(self, days: int = 1) -> float:
        """Sum final totals for local calendar day(s), not rolling 24h windows.

        - ``days == 1``: today only (machine local date).
        - ``days > 1``: today and the previous ``days - 1`` calendar days inclusive.
        """
        if days < 1:
            return 0.0
        today = datetime.now().date()
        if days == 1:
            allowed_dates = {today}
        else:
            allowed_dates = {today - timedelta(days=i) for i in range(days)}
        total = 0.0
        for receipt in self._sales_history:
            sale_date = receipt.created_date.date()
            if sale_date in allowed_dates:
                total += receipt.calculate_final_total()
        return total
