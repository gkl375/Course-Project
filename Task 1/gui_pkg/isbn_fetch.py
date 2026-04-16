"""
isbn_fetch.py - ISBN lookup and fetched metadata apply helpers.
"""

from __future__ import annotations

import threading

import requests
import tkinter as tk
from tkinter import messagebox

from api_client import ISBNLookup
import utils


def fetch_isbn_details(self):
    """Fetch ISBN details from API (runs in background thread)."""
    isbn = self.add_isbn_entry.get().strip()
    if not utils.validate_isbn(isbn):
        messagebox.showerror("Error", "Invalid ISBN format (must be 13 digits)")
        return

    self.fetch_btn.config(state=tk.DISABLED)
    self.fetch_status_var.set("Fetching...")

    def do_fetch():
        data = ISBNLookup.fetch_isbn(isbn, self.inventory_manager.isbn_cache)
        self.root.after(0, self._on_isbn_fetched, isbn, data)

    threading.Thread(target=do_fetch, daemon=True).start()


def _on_isbn_fetched(self, isbn: str, data):
    """Called on the main thread when ISBN fetch completes."""
    self.fetch_btn.config(state=tk.NORMAL)
    self.fetch_status_var.set("")
    if data:
        self.add_title_entry.delete(0, tk.END)
        self.add_title_entry.insert(0, data["title"])
        self.add_subtitle_entry.delete(0, tk.END)
        self.add_subtitle_entry.insert(0, data.get("subtitle", ""))
        self.add_author_entry.delete(0, tk.END)
        self.add_author_entry.insert(0, data["authors"])
        self.add_publisher_entry.delete(0, tk.END)
        self.add_publisher_entry.insert(0, data.get("publisher", ""))
        self.add_pub_date_entry.delete(0, tk.END)
        self.add_pub_date_entry.insert(0, data.get("publication_date", ""))
        # Category/Subcategory are user-selected and not overwritten from API.
        self._last_fetched_isbn = isbn
        remote_cover_url = str(data.get("thumbnail", "") or data.get("cover_url", "")).strip()
        self._last_fetched_cover_url = remote_cover_url

        if remote_cover_url:

            def cache_worker():
                try:
                    resp = requests.get(remote_cover_url, timeout=8)
                    resp.raise_for_status()
                    local_path = self._save_cover_image_bytes(isbn, resp.content)

                    def apply():
                        if self._last_fetched_isbn == isbn:
                            self._last_fetched_cover_url = local_path

                    self.root.after(0, apply)
                except Exception:
                    pass

            threading.Thread(target=cache_worker, daemon=True).start()

        messagebox.showinfo("Success", f"Fetched: {data['title']}")
    else:
        messagebox.showerror(
            "Not Found",
            f"ISBN {isbn} not found in Google Books or Open Library",
        )
