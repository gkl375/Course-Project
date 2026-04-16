"""
sales.py - POS Sales Logic and Order Processing
"""

from typing import Optional
from models import Store, Order, Customer, Receipt


class SalesManager:
    """Manage point-of-sale operations."""
    
    def __init__(self, store: Store):
        """Initialize sales manager."""
        self.store = store
        self.current_order: Optional[Order] = None
        self.current_customer: Optional[Customer] = None
    
    def new_order(self) -> Order:
        """Create new order."""
        self.current_order = Order()
        return self.current_order
    
    def select_customer(self, customer_id: str) -> bool:
        """Select customer for order."""
        customer = self.store.get_customer(customer_id)
        if customer:
            self.current_customer = customer
            return True
        return False
    
    def add_to_cart(self, key: str, quantity: int = 1) -> bool:
        """Add product (Book by ISBN or Nonbook by GTIN) to current order."""
        if not self.current_order:
            self.new_order()
        product = self.store.get_product(key)
        if not product or quantity < 1:
            return False
        order = self.current_order
        if quantity == 1:
            pkey = product.get_product_key()
            qty_before = next(
                (i.quantity for i in order.get_items() if i.product.get_product_key() == pkey),
                0,
            )
            order + product  # Order.__add__: add one unit via +
            qty_after = next(
                (i.quantity for i in order.get_items() if i.product.get_product_key() == pkey),
                0,
            )
            return qty_after == qty_before + 1
        return order.add_item(product, quantity)
    
    def remove_from_cart(self, key: str) -> bool:
        """Remove product from cart by key (ISBN or GTIN)."""
        if not self.current_order:
            return False
        return self.current_order.remove_item(key)
    
    def update_cart_quantity(self, key: str, new_quantity: int) -> bool:
        """Update quantity for item in cart. If new_quantity <= 0, removes item."""
        if not self.current_order:
            return False
        return self.current_order.update_item_quantity(key, new_quantity)
    
    def process_checkout(self) -> Optional[Receipt]:
        """
        Process checkout and generate receipt.
        
        Returns:
            Receipt object or None if error
        """
        if not self.current_order or len(self.current_order) == 0:
            print("Error: Cart is empty")
            return None
        
        # Calculate discount
        discount_amount = 0.0
        if self.current_customer:
            discount_rate = self.current_customer.get_discount_rate()
            discount_amount = self.current_order.subtotal * discount_rate
        
        # Process sale
        receipt = self.store.process_sale(self.current_order, 
                                         self.current_customer)
        
        if receipt:
            self.current_order = None
            self.current_customer = None
            return receipt
        
        return None
    
    def cancel_order(self) -> None:
        """Cancel current order."""
        self.current_order = None
        self.current_customer = None
