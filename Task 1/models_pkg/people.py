"""
people.py - Person base class and concrete people (Customer, Supplier, Staff).
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional


class Person:
    """Base class for people in system."""

    def __init__(self, name: str, person_id: str, phone: str = "", email: str = ""):
        self._name = name
        self._person_id = person_id
        self._phone = (phone or "").strip()
        self._email = (email or "").strip()

    @property
    def name(self) -> str:
        return self._name

    @property
    def person_id(self) -> str:
        return self._person_id

    @property
    def phone(self) -> str:
        return self._phone

    @property
    def email(self) -> str:
        return self._email

    def update_info(
        self,
        name: Optional[str] = None,
        phone: Optional[str] = None,
        email: Optional[str] = None,
    ) -> None:
        if name is not None:
            self._name = str(name).strip() or self._name
        if phone is not None:
            self._phone = str(phone).strip()
        if email is not None:
            self._email = (email or "").strip()

    def __str__(self) -> str:
        return f"{self.name} (ID: {self.person_id})"

    def __eq__(self, other) -> bool:
        if isinstance(other, Person):
            return self._person_id == other._person_id
        return False


class Customer(Person):
    """Customer subclass with loyalty program."""

    def __init__(self, first_name: str, last_name: str, customer_id: str, telephone: str, email: str):
        full_name = f"{first_name} {last_name}".strip() or " "
        super().__init__(full_name, customer_id, phone=telephone, email=email)
        self._first_name = first_name.strip()
        self._last_name = last_name.strip()
        self._loyalty_points = 0
        self._total_spent = 0.0
        self._purchase_history: List[Dict] = []

    @property
    def first_name(self) -> str:
        return self._first_name

    @property
    def last_name(self) -> str:
        return self._last_name

    @property
    def loyalty_points(self) -> int:
        return self._loyalty_points

    @property
    def total_spent(self) -> float:
        return self._total_spent

    @property
    def telephone(self) -> str:
        return self.phone

    def update_info(
        self,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        telephone: Optional[str] = None,
        email: Optional[str] = None,
    ) -> None:
        if first_name is not None:
            self._first_name = first_name.strip()
        if last_name is not None:
            self._last_name = last_name.strip()
        if first_name is not None or last_name is not None:
            self._name = f"{self._first_name} {self._last_name}".strip() or self._name
        super().update_info(phone=telephone, email=email)

    def add_purchase(self, amount: float) -> None:
        points = int(amount / 10)
        self._loyalty_points += points
        self._total_spent += amount
        self._purchase_history.append(
            {"date": datetime.now().isoformat(), "amount": amount, "points_earned": points}
        )

    def get_discount_rate(self) -> float:
        if self._loyalty_points >= 2000:
            return 0.15
        if self._loyalty_points >= 1000:
            return 0.10
        if self._loyalty_points >= 500:
            return 0.075
        return 0.0

    def get_tier(self) -> str:
        if self._loyalty_points >= 2000:
            return "🥇 Gold"
        if self._loyalty_points >= 1000:
            return "🥈 Silver"
        if self._loyalty_points >= 500:
            return "🥉 Bronze"
        return "Standard"

    def __str__(self) -> str:
        return f"{self.name} ({self.loyalty_points}pts - {self.get_tier()})"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "first_name": self._first_name,
            "last_name": self._last_name,
            "customer_id": self._person_id,
            "telephone": self.phone,
            "email": self.email,
            "loyalty_points": self._loyalty_points,
            "total_spent": self._total_spent,
            "purchase_history": self._purchase_history,
        }


class Supplier(Person):
    """Supplier class for inventory sourcing (Book ISBN and Nonbook GTIN)."""

    def __init__(
        self,
        name: str,
        supplier_id: str,
        contact_person: str = "",
        address: str = "",
        phone: str = "",
        email: str = "",
        contact: str = "",
    ):
        super().__init__(name, supplier_id, phone=(phone or contact or "").strip(), email=email)
        self.contact_person = (contact_person or "").strip()
        self.address = (address or "").strip()
        self._catalog_prices: Dict[str, float] = {}

    def add_book(self, isbn: str) -> None:
        self.add_catalog_key(isbn, 0.0)

    def add_catalog_key(self, key: str, unit_price: float = 0.0) -> None:
        k = str(key).strip()
        if not k:
            return
        if k not in self._catalog_prices:
            self._catalog_prices[k] = float(unit_price)

    def get_catalog_unit_price(self, product_key: str, inventory_fallback: float) -> float:
        k = str(product_key).strip()
        if k in self._catalog_prices:
            return float(self._catalog_prices[k])
        return float(inventory_fallback)

    def update_info(
        self,
        name: Optional[str] = None,
        contact_person: Optional[str] = None,
        address: Optional[str] = None,
        phone: Optional[str] = None,
        email: Optional[str] = None,
    ) -> None:
        super().update_info(name=name, phone=phone, email=email)
        if contact_person is not None:
            self.contact_person = contact_person.strip()
        if address is not None:
            self.address = address.strip()

    def set_catalog_keys(self, keys: List[str]) -> None:
        seen: set[str] = set()
        new_prices: Dict[str, float] = {}
        for raw in keys:
            s = str(raw).strip()
            if not s or s in seen:
                continue
            seen.add(s)
            new_prices[s] = self._catalog_prices.get(s, 0.0)
        self._catalog_prices = new_prices

    def set_catalog_prices(self, mapping: Dict[str, float]) -> None:
        self._catalog_prices = {
            str(k).strip(): float(v) for k, v in mapping.items() if str(k).strip()
        }

    @property
    def catalog_keys(self) -> List[str]:
        return list(self._catalog_prices.keys())

    @property
    def catalog_prices(self) -> Dict[str, float]:
        return dict(self._catalog_prices)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self._name,
            "supplier_id": self._person_id,
            "contact_person": self.contact_person,
            "address": self.address,
            "phone": self.phone,
            "email": self.email,
            "supplied_catalog": dict(self._catalog_prices),
        }


class Staff(Person):
    """Staff member information."""

    def __init__(
        self,
        name: str,
        staff_id: str,
        role: str = "",
        phone: str = "",
        email: str = "",
        active: bool = True,
    ):
        super().__init__(name, staff_id, phone=phone, email=email)
        self.role = (role or "").strip()
        self.active = bool(active)

    def update_info(
        self,
        name: Optional[str] = None,
        role: Optional[str] = None,
        phone: Optional[str] = None,
        email: Optional[str] = None,
        active: Optional[bool] = None,
    ) -> None:
        super().update_info(name=name, phone=phone, email=email)
        if role is not None:
            self.role = role.strip()
        if active is not None:
            self.active = bool(active)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "staff_id": self.person_id,
            "role": self.role,
            "phone": self.phone,
            "email": self.email,
            "active": self.active,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Staff":
        return cls(
            name=str(d.get("name", "")).strip(),
            staff_id=str(d.get("staff_id", "")).strip(),
            role=str(d.get("role", "")).strip(),
            phone=str(d.get("phone", "")).strip(),
            email=str(d.get("email", "")).strip(),
            active=bool(d.get("active", True)),
        )
