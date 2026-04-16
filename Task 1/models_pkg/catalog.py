"""
catalog.py - Product abstractions and concrete catalog items (Book, NonBook).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
import math
from typing import Any, Dict, List, Optional


class Product(ABC):
    """Abstract base class for sellable products."""

    def __init__(self, name: str, price: float):
        self.name = name
        self.price = price
        self._stock = 0
        self.minimum_stock_level: int = 0
        self.maximum_stock_level: int = 0
        self.lead_time_days: int = 0
        self.average_daily_sales: float = 0.0
        self.default_supplier_id: str = ""
        self.reorder_enabled: bool = False

    @property
    def stock(self) -> int:
        return self._stock

    @stock.setter
    def stock(self, value: int):
        if value < 0:
            raise ValueError("Stock cannot be negative")
        self._stock = value

    @abstractmethod
    def get_product_key(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def product_type_name(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        raise NotImplementedError

    def get_price(self) -> float:
        return float(self.price)

    def is_available(self) -> bool:
        return self._stock > 0

    def update_stock(self, quantity: int) -> bool:
        if quantity > self._stock:
            return False
        self._stock -= quantity
        return True

    def __str__(self) -> str:
        return f"{self.name} (HKD {self.price:.2f})"

    def __eq__(self, other) -> bool:
        if isinstance(other, Product):
            return self.name == other.name
        return False

    def reorder_level(self) -> int:
        level = float(self.minimum_stock_level) + (
            float(self.lead_time_days) * float(self.average_daily_sales)
        )
        return max(0, int(math.ceil(level)))

    def update_reorder_params(
        self,
        minimum_stock_level: Optional[int] = None,
        maximum_stock_level: Optional[int] = None,
        lead_time_days: Optional[int] = None,
        average_daily_sales: Optional[float] = None,
        default_supplier_id: Optional[str] = None,
        reorder_enabled: Optional[bool] = None,
    ) -> None:
        if minimum_stock_level is not None:
            self.minimum_stock_level = max(0, int(minimum_stock_level))
        if maximum_stock_level is not None:
            self.maximum_stock_level = max(0, int(maximum_stock_level))
        if lead_time_days is not None:
            self.lead_time_days = max(0, int(lead_time_days))
        if average_daily_sales is not None:
            self.average_daily_sales = max(0.0, float(average_daily_sales))
        if default_supplier_id is not None:
            self.default_supplier_id = str(default_supplier_id).strip()
        if reorder_enabled is not None:
            self.reorder_enabled = bool(reorder_enabled)


class Book(Product):
    BOOK_CATEGORIES: Dict[str, List[str]] = {
        "Art & Design": [
            "Architecture", "Art History & Theory", "Design & Graphic Design",
            "Fashion Design", "Interior Design", "Film & Television",
            "Music, Dance & Theater", "Photography", "Product Design",
        ],
        "Audio": ["Audiobooks", "Music CDs"],
        "Business & Economics": [
            "Accounting", "Business & Self-Help", "Career Development",
            "Business Communication", "Economics", "Finance", "Human Resources",
            "Investment", "Management", "Management Information Systems", "Marketing",
        ],
        "China & Hong Kong Studies": ["Hong Kong & Macau", "Mainland China & Taiwan"],
        "Cooking & Food": [
            "Asian Cuisine", "European Cuisine", "Professional Cooking",
            "Party Food & Desserts", "Quick Recipes", "Vegetarian & Healthy Cooking",
            "General & Miscellaneous",
        ],
        "Education & Teaching": [
            "General Education", "Study Skills", "Teaching Manuals", "Teaching Resources",
        ],
        "Humanities & Literature": [
            "Asian & African Studies", "Biography", "Classics", "Fiction",
            "History", "Philosophy", "Religion",
        ],
        "Inner Exploration": ["Human Bonds", "Personal Wellness", "Spirit & Faith"],
        "Language Learning & Linguistics": [
            "Cantonese", "English", "French", "German", "Italian", "Japanese",
            "Mandarin", "Spanish", "Other Languages", "Linguistics & Writing",
        ],
        "Law": ["Legal Studies"],
        "Lifestyle & Leisure": [
            "Pets & Animals", "Collectibles", "Fashion & Beauty", "Games", "Gardening",
            "Health & Wellness", "Humor", "Medicine", "Military & Automotive",
            "New Age & Spirituality", "Parenting", "Pregnancy", "Sex & Relationships",
            "Sports", "Wine & Beverages",
        ],
        "Reference Works": [
            "Encyclopedias",
            "Dictionaries (English, English-Chinese, French, German, Italian, Japanese, Spanish, Other)",
        ],
        "Science, Technology & Math": [
            "Popular Science", "Higher Education & Applied Sciences", "Technology & Engineering",
            "Computer Studies (Applications, Programming Languages, Mobile & Handheld, Office Software, CD-ROM)",
            "Mathematics", "Environmental Science",
        ],
        "Self-Help & Personal Development": ["Self-Help", "Relationships", "Spirituality & Religion"],
        "Social Sciences": ["Sociology", "Psychology", "Politics & Current Affairs", "Anthropology"],
        "Study Aids & Test Prep": [
            "A-Level", "ACCA", "CFA", "CPA", "GCSE", "GMAT", "IB", "IELTS", "SAT", "TOEFL", "Other Exams",
        ],
        "Travel": ["Guidebooks", "Travel Literature", "Maps & Atlases"],
        "Young Adult & Teen": ["Comics", "Early Readers", "Teen Fiction", "Teen Science & Tech"],
        "General": [],
    }

    def __init__(self, name: str, price: float, isbn: str, author: str, category: str = "General", subcategory: str = ""):
        super().__init__(name, price)
        self.isbn = str(isbn).strip()
        self.author = author
        self.category = category
        self.subcategory = (subcategory or "").strip()
        self.cover_url = ""
        self.publisher = ""
        self.pages = 0
        self.subtitle = ""
        self.publication_date = ""
        self.subject = ""

    def get_product_key(self) -> str:
        return self.isbn

    def product_type_name(self) -> str:
        return "Book"

    def __str__(self) -> str:
        return f"{self.name} by {self.author} (ISBN: {self.isbn})"

    def __eq__(self, other) -> bool:
        if isinstance(other, Book):
            return self.isbn == other.isbn
        return False

    def __repr__(self) -> str:
        return f"Book(isbn='{self.isbn}', title='{self.name}', price={self.price})"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "isbn": self.isbn,
            "author": self.author,
            "price": self.price,
            "stock": self.stock,
            "minimum_stock_level": self.minimum_stock_level,
            "maximum_stock_level": self.maximum_stock_level,
            "lead_time_days": self.lead_time_days,
            "average_daily_sales": self.average_daily_sales,
            "default_supplier_id": self.default_supplier_id,
            "reorder_enabled": bool(getattr(self, "reorder_enabled", False)),
            "category": self.category,
            "subcategory": self.subcategory,
            "publisher": self.publisher,
            "pages": self.pages,
            "cover_url": self.cover_url,
            "subtitle": self.subtitle,
            "publication_date": self.publication_date,
            "subject": self.subject,
        }


class NonBook(Product):
    NONBOOK_CATEGORIES: Dict[str, List[str]] = {
        "Packaging Supplies": [
            "Packing Twine / Nylon Rope", "Rubber Bands", "Bubble Wrap", "Gift Boxes",
            "Wrapping Paper", "Gift Bags", "Cable Ties", "Waterproof Paper / Kraft Paper",
            "Other Packaging Supplies",
        ],
        "Seasonal Stationery": [
            "Yearly Diaries", "Yearly / Monthly / Daily Calendars", "Christmas Decorations",
            "Chinese New Year Decorations", "Other Seasonal Products",
        ],
        "Filing & Storage": [
            "Document Boxes / Racks / Cabinets", "Magazine Racks", "Expanding Files", "File Folders",
            "Ring Binders", "Clear Books", "Business Card Holders", "Document Envelopes", "Zipper Bags",
            "Indexes", "File Refills", "Other Filing Supplies",
        ],
        "Paper Products": [
            "Address & Phone Books", "Calligraphy Paper", "Cards", "Cash Register / Calculator Rolls",
            "Cardboard / Corrugated Paper", "Clips / Invoices / Account Books / Leases", "Coloring Books",
            "Colored Paper", "Copy Paper", "Drawing Books", "Drawing Paper", "Envelopes", "Fax Paper",
            "Gift Envelopes / Red Packets", "Graph Paper", "Hardcover Notebooks", "Letter Paper / Stationery Sets",
            "Loose-leaf Notebooks", "Loose-leaf Paper", "Manuscript Paper", "Memo Pads", "Postcards",
            "Sticky Notes", "Single-lined Notebooks", "Single-lined Paper", "Spiral Notebooks",
            "Stamp Albums", "Sticker Books", "Tracing Paper", "Other Paper Products", "Other Notebooks",
        ],
        "Writing Instruments": [
            "Ballpoint Pens / Refills", "Gel Pens / Refills",
            "Fountain Pens / Ink / Cartridges / Converters", "Multi-function Pens",
            "Brush Pens / Calligraphy Pens", "Oil-based Paint Markers",
            "Whiteboard Markers / Refills", "Permanent Markers / Refills", "Chalk",
            "Art Brushes", "Highlighters", "Pencils / Leads / Mechanical Pencils",
            "Other Pens / Refills / Writing Accessories",
        ],
        "Office Equipment & Supplies": [
            "Hole Punches", "Staplers / Staples", "Binding Rings", "Utility Knives / Cutters",
            "Scissors", "Paper Trimmers / Guillotines",
            "Correction Fluid / Correction Tape / Other Correction Supplies", "Erasers",
            "Pencil Sharpeners", "Pencil Cases / Bags / Holders / Extenders",
            "Glue / Adhesive Tape / Tape Dispensers / Adhesive Putty",
            "Binder Clips / Paper Clips / Paper Clip Holders", "Laminating Pouches",
            "Book Covers / Protective Covers", "Whiteboards / Chalkboards / Erasers",
            "Book Stands / Bookends", "Corkboards / Water Dispensers", "Magnetic Accessories",
            "Tape Measures / Rulers / Drawing Rulers", "Letter Openers", "Compasses",
            "Magnifying Glasses", "Notice Signs / Name Card Holders / Business Card Holders",
            "Stamp Pads / Ink / Stamp Ink / Self-inking Stamps / Date Stamps", "Decorative Stamps",
            "Pricing Guns / Ink Rollers", "Batteries / Chargers",
            "Manual Paper Shredders / Demo Models / Belts", "ID Badges / Badge Holders",
            "Solar Film", "Stationery Sets", "Wallpaper", "Other Office Equipment & Supplies",
        ],
        "Gifts & Premiums": [
            "Anime / Comic Merchandise", "Arts & Crafts Collectibles", "Figurines / Ornaments",
            "Storage Boxes", "Travel Accessories", "Backpacks / School Bags", "Bookmarks",
            "Party Supplies / Balloons", "Reusable Bags",
            "Photo Frames / Photo Albums / Autograph Books",
            "Ribbons / Decorative Adhesive Tape / Stickers", "Wallets / Coin Purses",
            "Coin Collectibles", "Music Boxes", "Candles / Candle Accessories", "Other Bags",
            "Other Entertainment & Gift Items",
        ],
        "Household Items": [
            "Furniture", "Kitchenware / Tableware", "Bedding", "Towels", "Apparel / Footwear",
            "Accessories", "Personal Care Products", "Medical / First Aid Supplies", "Home Appliances",
            "Lamps / Fans", "Food / Beverages", "Water Bottles / Flasks / Cups", "Rain Gear",
            "Eyeglasses / Cases", "Headphones / Earphones", "Aprons / Gloves", "Potted Plants",
            "Other Household Items",
        ],
    }

    def __init__(self, name: str, price: float, gtin: str, category: str, subcategory: str = "", brand: str = "", model: str = ""):
        super().__init__(name, price)
        self.gtin = str(gtin).strip()
        self.category = category
        self.subcategory = (subcategory or "").strip()
        self.brand = brand
        self.model = model
        self.product_image = ""

    def get_product_key(self) -> str:
        return self.gtin

    def product_type_name(self) -> str:
        return "Nonbook"

    def __str__(self) -> str:
        return f"{self.name} (GTIN: {self.gtin}, HKD {self.price:.2f})"

    def __eq__(self, other) -> bool:
        if isinstance(other, NonBook):
            return self.gtin == other.gtin
        return False

    def __repr__(self) -> str:
        return f"Nonbook(gtin='{self.gtin}', name='{self.name}', price={self.price})"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "price": self.price,
            "stock": self.stock,
            "minimum_stock_level": self.minimum_stock_level,
            "maximum_stock_level": self.maximum_stock_level,
            "lead_time_days": self.lead_time_days,
            "average_daily_sales": self.average_daily_sales,
            "default_supplier_id": self.default_supplier_id,
            "reorder_enabled": bool(getattr(self, "reorder_enabled", False)),
            "gtin": self.gtin,
            "category": self.category,
            "subcategory": self.subcategory,
            "brand": getattr(self, "brand", ""),
            "model": getattr(self, "model", ""),
            "product_image": getattr(self, "product_image", "") or "",
        }
