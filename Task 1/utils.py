"""
utils.py - Utility Functions and Helpers
"""

import os
import json
from typing import Dict, Any


def generate_receipt_id() -> str:
    """Generate sequential receipt ID starting from 1."""
    # Fixed-width sequence to keep receipts sortable and consistent (e.g. RCP000001).
    return f"RCP{next_sequence('receipt'):06d}"


def generate_customer_id() -> str:
    """Generate sequential customer ID: CUS0001, CUS0002, ..."""
    return f"CUS{next_sequence('customer'):04d}"


def generate_supplier_id() -> str:
    """Generate sequential supplier ID: SUP0001, SUP0002, ..."""
    return f"SUP{next_sequence('supplier'):04d}"


def generate_purchase_order_id() -> str:
    """Generate sequential purchase order ID: PO0001, PO0002, ..."""
    return f"PO{next_sequence('purchase_order'):04d}"


def generate_staff_id() -> str:
    """Generate sequential staff ID: STF0001, STF0002, ..."""
    return f"STF{next_sequence('staff'):04d}"


def _counters_path() -> str:
    return os.path.join("data", "id_counters.json")


def _load_counters() -> Dict[str, int]:
    path = _counters_path()
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data: Any = json.load(f)
        if isinstance(data, dict):
            out: Dict[str, int] = {}
            for k, v in data.items():
                try:
                    out[str(k)] = int(v)
                except Exception:
                    continue
            return out
    except Exception:
        return {}
    return {}


def _save_counters(counters: Dict[str, int]) -> None:
    path = _counters_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(counters, f, indent=2, ensure_ascii=False)


def next_sequence(key: str) -> int:
    """Get next sequence number for a given key (starts from 1)."""
    k = str(key).strip()
    counters = _load_counters()
    n = int(counters.get(k, 0) or 0) + 1
    counters[k] = n
    _save_counters(counters)
    return n


def validate_isbn(isbn: str) -> bool:
    """Validate ISBN-13 format."""
    if len(isbn) != 13 or not isbn.isdigit():
        return False
    return True
