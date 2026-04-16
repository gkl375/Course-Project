"""
orders.py - Order, receipt, and purchase-order models.
"""

from __future__ import annotations

import copy
from datetime import datetime
import random
import textwrap
from typing import Any, Dict, List, Optional

import utils


class OrderItem:
    """Represents an item in an order (Book or Nonbook)."""

    def __init__(self, product: "Product", quantity: int):
        self.product = product
        self.quantity = quantity

    def get_subtotal(self) -> float:
        return self.product.price * self.quantity

    def __str__(self) -> str:
        return f"{self.product.name} ×{self.quantity} = HKD{self.get_subtotal():.2f}"


class _ReceiptCustomerSnapshot:
    """Loyalty state exactly as printed on the receipt (post-``add_purchase``)."""

    __slots__ = ("name", "person_id", "_loyalty_points", "_loyalty_tier")

    def __init__(self, name: str, person_id: str, loyalty_points: int, loyalty_tier: str):
        self.name = str(name or "").strip() or " "
        self.person_id = str(person_id or "").strip()
        self._loyalty_points = int(loyalty_points)
        self._loyalty_tier = str(loyalty_tier or "Standard")

    @property
    def loyalty_points(self) -> int:
        return self._loyalty_points

    def get_tier(self) -> str:
        return self._loyalty_tier


class Order:
    """Shopping cart and order management (Book and Nonbook)."""

    def __init__(self, order_id: str = ""):
        self.order_id = order_id or f"ORD{random.randint(100000, 999999)}"
        self._cart: List[OrderItem] = []

    def add_item(self, product: "Product", quantity: int = 1) -> bool:
        if not product.is_available() or quantity > product.stock:
            return False
        key = product.get_product_key()
        for item in self._cart:
            if item.product.get_product_key() == key:
                item.quantity += quantity
                return True
        self._cart.append(OrderItem(product, quantity))
        return True

    def remove_item(self, key: str) -> bool:
        for i, item in enumerate(self._cart):
            if item.product.get_product_key() == key:
                self._cart.pop(i)
                return True
        return False

    def update_item_quantity(self, key: str, new_quantity: int) -> bool:
        if new_quantity <= 0:
            return self.remove_item(key)
        for item in self._cart:
            if item.product.get_product_key() == key:
                if new_quantity > item.product.stock:
                    return False
                item.quantity = new_quantity
                return True
        return False

    def get_items(self) -> List[OrderItem]:
        return self._cart

    @property
    def subtotal(self) -> float:
        return sum(item.get_subtotal() for item in self._cart)

    @property
    def total(self) -> float:
        return self.subtotal

    def __len__(self) -> int:
        return len(self._cart)

    def __str__(self) -> str:
        return f"Order {self.order_id}: {len(self._cart)} items, HKD {self.total:.2f}"

    def __add__(self, product: "Product") -> "Order":
        """Magic method: ``order + product`` adds one unit (delegates to :meth:`add_item`)."""
        self.add_item(product, 1)
        return self


class Receipt:
    """Receipt generation and formatting."""

    def __init__(
        self,
        order: Order,
        customer: Optional["Customer"] = None,
        discount_amount: float = 0.0,
        *,
        receipt_id: Optional[str] = None,
        created_date: Optional[datetime] = None,
    ):
        self.receipt_id = receipt_id if receipt_id else utils.generate_receipt_id()
        self.order = order
        self.customer = customer
        self.discount_amount = discount_amount
        self.created_date = created_date if created_date is not None else datetime.now()
        self.store_name = "ABC Bookstore"

    @classmethod
    def from_saved_dict(cls, row: Dict[str, Any], store: Any) -> "Receipt":
        """Rebuild a receipt from persisted JSON so :meth:`to_string` matches post-checkout layout."""
        from models import Book, NonBook

        order = Order()
        for it in row.get("items") or []:
            key = str(it.get("key", "")).strip()
            qty = int(it.get("qty", 0) or 0)
            if qty < 1 or not key:
                continue
            unit = float(it.get("unit_price", 0) or 0)
            display_name = str(it.get("name", "") or "").strip() or key
            p = store.get_product(key)
            if p:
                p = copy.copy(p)
                p.price = unit
                p.name = display_name
            else:
                if key.startswith("978"):
                    p = Book(display_name, unit, key, "—", "General", "")
                else:
                    p = NonBook(display_name, unit, key, "General", "", "", "")
                p._stock = 999999
            order._cart.append(OrderItem(p, qty))

        customer = None
        snap = row.get("customer_snapshot")
        if isinstance(snap, dict) and str(snap.get("customer_id") or "").strip():
            customer = _ReceiptCustomerSnapshot(
                str(snap.get("name") or ""),
                str(snap.get("customer_id") or ""),
                int(snap.get("loyalty_points", 0) or 0),
                str(snap.get("loyalty_tier") or "Standard"),
            )
        else:
            cust_raw = row.get("customer")
            if isinstance(cust_raw, dict):
                cid = str(cust_raw.get("customer_id") or "").strip()
                if cid:
                    customer = store.get_customer(cid)

        discount = float(row.get("discount_amount", 0) or 0)
        rid = str(row.get("receipt_id") or "").strip() or None

        created_date: Optional[datetime] = None
        created_raw = str(row.get("created", "")).strip()
        if created_raw:
            try:
                created_date = datetime.fromisoformat(created_raw.replace("Z", "+00:00"))
                if created_date.tzinfo is not None:
                    created_date = created_date.replace(tzinfo=None)
            except ValueError:
                created_date = None

        rec = cls(order, customer, discount, receipt_id=rid, created_date=created_date)
        saved_store = str(row.get("receipt_store_name") or "").strip()
        if saved_store:
            rec.store_name = saved_store
        else:
            rec.store_name = str(getattr(store, "bookstore_name", "") or "").strip() or "ABC Bookstore"
        return rec

    def calculate_final_total(self) -> float:
        return self.order.subtotal - self.discount_amount

    def to_string(self) -> str:
        receipt_width = 64
        col_sep = " | "
        sep_len = len(col_sep)
        w_qty, w_price = 6, 12
        w_item = receipt_width - w_qty - w_price - 2 * sep_len
        if w_item < 18:
            w_item = 18
        table_width = w_item + sep_len + w_qty + sep_len + w_price

        separator = "=" * table_width
        lines: list[str] = []

        lines.append(separator)
        store_name = str(getattr(self, "store_name", "") or "").strip() or "ABC Bookstore"
        _title = f"{store_name.upper()} - RECEIPT"
        lines.append(_title.center(table_width) if len(_title) < table_width else _title)
        lines.append(separator)
        lines.append(f"Receipt ID: {self.receipt_id}")
        lines.append(f"Date: {self.created_date.strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(separator)

        customer = self.customer
        if customer is not None:
            lines.append(f"Customer: {customer.name}")
            lines.append(f"Customer ID: {customer.person_id}")
            lines.append(f"Loyalty Tier: {customer.get_tier()}")
            lines.append(f"Loyalty Points: {customer.loyalty_points}")

        items = self.order.get_items()
        lines.append(
            f"{'ITEM':<{w_item}}{col_sep}{'QTY':^{w_qty}}{col_sep}{'SUBTOTAL':>{w_price}}"
        )
        lines.append("-" * table_width)
        if not items:
            lines.append("(no items)")
        for item in items:
            name = str(getattr(item.product, "name", "") or "").strip()
            key = str(item.product.get_product_key()).strip()
            display_name = name if name else key
            if key and key not in display_name:
                display_name = f"{display_name} ({key})"
            line_total = float(item.get_subtotal())
            price_str = f"HKD {line_total:.2f}"
            chunks = textwrap.wrap(
                display_name,
                width=w_item,
                break_long_words=True,
                break_on_hyphens=True,
            )
            if not chunks:
                chunks = [""]
            empty_qty = f"{'':^{w_qty}}"
            empty_price = f"{'':>{w_price}}"
            for i, chunk in enumerate(chunks):
                if i == 0:
                    lines.append(
                        f"{chunk:<{w_item}}{col_sep}{item.quantity:^{w_qty}}{col_sep}{price_str:>{w_price}}"
                    )
                else:
                    lines.append(
                        f"{chunk:<{w_item}}{col_sep}{empty_qty}{col_sep}{empty_price}"
                    )

        lines.append(separator)

        def _summary_line(label: str, value: str, line_width: int = table_width) -> str:
            left = f"{label}:"
            pad = line_width - len(left) - len(value)
            if pad < 1:
                return f"{left} {value}"
            return left + (" " * pad) + value

        lines.append(_summary_line("Subtotal", f"HKD {self.order.subtotal:.2f}"))

        if self.discount_amount > 0 and self.order.subtotal > 0:
            rate = (self.discount_amount / self.order.subtotal) * 100
            label = f"Loyalty Discount ({rate:.1f}%)"
            disc = f"-HKD {self.discount_amount:.2f}"
            lines.append(_summary_line(label, disc))

        final_total = max(0.0, self.calculate_final_total())
        if customer is not None:
            points_earned = max(0, int(final_total / 10))
            lines.append(_summary_line("Points Earned", str(points_earned)))

        lines.append(separator)
        lines.append(_summary_line("TOTAL", f"HKD {final_total:.2f}"))
        lines.append(separator)
        _thanks = f"Thank you for shopping at {store_name}!"
        lines.append(_thanks.center(table_width) if len(_thanks) < table_width else _thanks)
        lines.append(separator)

        return "\n".join(lines)

    def __str__(self) -> str:
        return self.to_string()

    def to_dict(self, include_text: bool = True) -> Dict[str, Any]:
        customer = self.customer
        items_out: List[Dict[str, Any]] = []
        for it in self.order.get_items():
            key = str(it.product.get_product_key()).strip()
            name = str(getattr(it.product, "name", "") or "").strip()
            unit = float(getattr(it.product, "price", 0.0) or 0.0)
            qty = int(getattr(it, "quantity", 0) or 0)
            items_out.append(
                {
                    "key": key,
                    "name": name,
                    "qty": qty,
                    "unit_price": unit,
                    "subtotal": float(unit * qty),
                }
            )
        subtotal = float(self.order.subtotal)
        discount = float(self.discount_amount)
        final_total = float(max(0.0, self.calculate_final_total()))
        d: Dict[str, Any] = {
            "receipt_id": self.receipt_id,
            "created": self.created_date.isoformat(timespec="seconds"),
            "customer": (
                {
                    "customer_id": customer.person_id,
                    "name": customer.name,
                    "email": getattr(customer, "email", "") or "",
                    "telephone": getattr(customer, "telephone", "") or "",
                }
                if customer is not None
                else None
            ),
            "items": items_out,
            "subtotal": subtotal,
            "discount_amount": discount,
            "final_total": final_total,
            "receipt_store_name": str(getattr(self, "store_name", "") or "").strip() or "ABC Bookstore",
        }
        if customer is not None:
            d["customer_snapshot"] = {
                "customer_id": customer.person_id,
                "name": customer.name,
                "loyalty_points": int(customer.loyalty_points),
                "loyalty_tier": customer.get_tier(),
            }
        if include_text:
            d["receipt_text"] = self.to_string()
        return d


class PurchaseOrderLine:
    """One line on a purchase order (Book ISBN or Nonbook GTIN)."""

    def __init__(self, product_key: str, quantity: int, unit_price: float = 0.0):
        self.product_key = str(product_key).strip()
        self.quantity = max(1, int(quantity))
        self.unit_price = float(unit_price)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "product_key": self.product_key,
            "quantity": self.quantity,
            "unit_price": self.unit_price,
        }

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "PurchaseOrderLine":
        return PurchaseOrderLine(
            d["product_key"],
            int(d.get("quantity", 1)),
            float(d.get("unit_price", 0) or 0),
        )


class PurchaseOrder:
    """Purchase order to a supplier (restock Book / Nonbook)."""

    VALID_STATUSES = ("Draft", "Sent", "Received", "Cancelled")

    def __init__(
        self,
        supplier_id: str,
        lines: Optional[List[PurchaseOrderLine]] = None,
        po_id: str = "",
        notes: str = "",
        status: str = "Draft",
        created: Optional[datetime] = None,
    ):
        self.po_id = po_id or utils.generate_purchase_order_id()
        self.supplier_id = str(supplier_id).strip()
        self.lines: List[PurchaseOrderLine] = lines or []
        self.created = created or datetime.now()
        self.notes = (notes or "").strip()
        self.status = status if status in self.VALID_STATUSES else "Draft"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "po_id": self.po_id,
            "supplier_id": self.supplier_id,
            "created": self.created.isoformat(timespec="seconds"),
            "status": self.status,
            "notes": self.notes,
            "lines": [ln.to_dict() for ln in self.lines],
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "PurchaseOrder":
        lines = [PurchaseOrderLine.from_dict(x) for x in d.get("lines", [])]
        po = cls(
            supplier_id=d["supplier_id"],
            lines=lines,
            po_id=d.get("po_id") or "",
            notes=d.get("notes", ""),
            status=d.get("status", "Draft"),
            created=None,
        )
        raw = d.get("created")
        if raw:
            try:
                po.created = datetime.fromisoformat(raw)
            except ValueError:
                pass
        return po

    def format_document(self, store: "Store") -> str:
        table_w = 75
        sep = "=" * table_w
        thin = "-" * table_w

        def _indented_block(first_line: str, *parts: str) -> List[str]:
            out: List[str] = [first_line]
            for p in parts:
                if not (p or "").strip():
                    continue
                for line in str(p).strip().splitlines():
                    line = line.strip()
                    if line:
                        out.append(f"  {line}")
            return out

        lines: List[str] = [sep, "PURCHASE ORDER".center(table_w), sep]

        buyer_name = (store.bookstore_name or "").strip() or "ABC Bookstore"
        lines += _indented_block(buyer_name, store.bookstore_address)
        if (store.bookstore_contact_name or "").strip():
            lines.append(f"  Contact: {store.bookstore_contact_name.strip()}")
        if (store.bookstore_phone or "").strip():
            lines.append(f"  Contact No.: {store.bookstore_phone.strip()}")
        if (store.bookstore_email or "").strip():
            lines.append(f"  Email: {store.bookstore_email.strip()}")
        lines.append("")

        sup = store.get_supplier(self.supplier_id)
        sup_name = sup.name if sup else "(unknown supplier)"
        lines += _indented_block("Supplier", sup_name, sup.address if sup else "")
        if sup:
            if (sup.contact_person or "").strip():
                lines.append(f"  Attn: {sup.contact_person.strip()}")
            if (sup.phone or "").strip():
                lines.append(f"  Contact No.: {sup.phone.strip()}")
            if (sup.email or "").strip():
                lines.append(f"  Email: {sup.email.strip()}")
        lines.append(f"  Supplier ID: {self.supplier_id}")
        lines.append("")
        lines.append(sep)
        lines.append(f"PO #:     {self.po_id}")
        lines.append(f"Date:     {self.created.strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(thin)
        lines.append("ITEMS")
        lines.append(thin)
        hdr = (
            f"{'#':>3}  {'ISBN / GTIN - Product Name':<38}  {'Qty':>4}  "
            f"{'Unit HKD':>10}  {'Subtotal':>12}"
        )
        lines.append(hdr)
        lines.append(thin)

        def _resolved_unit_price(ln: "PurchaseOrderLine", sup_obj: Optional["Supplier"]) -> float:
            if ln.unit_price > 0:
                return ln.unit_price
            p = store.get_product(ln.product_key)
            fb = float(p.price) if p else 0.0
            if sup_obj:
                return sup_obj.get_catalog_unit_price(ln.product_key, fb)
            return fb

        grand_total = 0.0
        # Align wrapped title under the key column (after "  #  ").
        name_ind = "     "
        name_tw = textwrap.TextWrapper(
            width=table_w,
            initial_indent=name_ind,
            subsequent_indent=name_ind,
            break_long_words=True,
            break_on_hyphens=True,
        )
        for i, ln in enumerate(self.lines, start=1):
            p = store.get_product(ln.product_key)
            key_disp = (ln.product_key[:38]).ljust(38)
            unit = _resolved_unit_price(ln, sup)
            ln_amt = unit * ln.quantity
            grand_total += ln_amt
            lines.append(
                f"{i:>3}  {key_disp}  {ln.quantity:>4}  "
                f"{unit:>10.2f}  {ln_amt:>12.2f}"
            )
            full_name = ((p.name if p else "(unknown)") or "(unknown)").strip()
            lines.extend(name_tw.wrap(full_name))
        lines.append(thin)
        lines.append(f"{'TOTAL (HKD)':>{table_w - 13}} {grand_total:>12.2f}")
        lines.append(sep)
        if self.notes:
            lines.append("Notes:")
            for note_line in self.notes.splitlines():
                stripped = note_line.strip()
                if stripped:
                    lines.append(stripped)
            lines.append(sep)
        lines.append("End of PO")
        return "\n".join(lines)
