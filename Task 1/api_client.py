"""
api_client.py - ISBN Lookup from Public APIs
"""

import requests
import json
from typing import Optional, Dict, Any
import time


class ISBNLookup:
    """Fetch book details from public ISBN APIs."""
    
    GOOGLE_BOOKS_URL = "https://www.googleapis.com/books/v1/volumes"
    OPENLIBRARY_URL = "https://openlibrary.org/api/books"
    GOOGLE_API_KEY = None  # Set your API key here or via environment variable
    
    @classmethod
    def set_api_key(cls, api_key: str):
        """Set Google Books API key."""
        cls.GOOGLE_API_KEY = api_key
        print(f"Google Books API key configured")
    
    @staticmethod
    def validate_isbn(isbn: str) -> bool:
        """Validate ISBN-13 format."""
        if len(isbn) != 13 or not isbn.isdigit():
            return False
        return True
    
    @staticmethod
    def fetch_google_books(isbn: str, timeout: int = 5, max_retries: int = 1) -> Optional[Dict[str, Any]]:
        """
        Fetch book details from Google Books API with minimal retry logic.
        
        Args:
            isbn: ISBN-13 code
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts (minimal to avoid delays)
        
        Returns:
            Dictionary with book details or None
        """
        try:
            # Try order:
            # 1) Google with key (if configured)
            # 2) Google without key (if key attempt fails)
            # This preserves Google as primary source before Open Library fallback.
            use_key_options = [True, False] if ISBNLookup.GOOGLE_API_KEY else [False]
            for use_key in use_key_options:
                for _ in range(max_retries):
                    params = {'q': f'isbn:{isbn}'}
                    if use_key and ISBNLookup.GOOGLE_API_KEY:
                        params['key'] = ISBNLookup.GOOGLE_API_KEY

                    response = requests.get(
                        ISBNLookup.GOOGLE_BOOKS_URL,
                        params=params,
                        timeout=timeout,
                    )

                    # Handle rate limiting - fail fast to use fallback
                    if response.status_code == 429:
                        print("Google Books API rate limited - using fallback")
                        return None

                    # If keyed request fails auth/permission, retry once without key.
                    if use_key and response.status_code in (400, 401, 403):
                        print("Google Books API key invalid/forbidden - retrying without key")
                        break

                    response.raise_for_status()
                    data = response.json()
                
                    items = data.get('items', [])
                    if not items:
                        return None

                    # Choose the best volume/image across all results.
                    # We prefer higher-resolution sizes and (slightly) prefer ebook formats.
                    size_order = ['extraLarge', 'large', 'medium', 'small', 'thumbnail', 'smallThumbnail']
                    best_volume = None
                    best_thumb_url = ''
                    best_score = -1

                    for item in items:
                        volume = item.get('volumeInfo', {}) or {}
                        image_links = volume.get('imageLinks', {}) or {}
                        if not image_links:
                            continue

                        # Base score from image size
                        for idx, size_name in enumerate(size_order):
                            url = image_links.get(size_name)
                            if not url:
                                continue
                            size_score = len(size_order) - idx  # extraLarge=6, ..., smallThumbnail=1
                            # Prefer ebook format slightly if available
                            sale_info = item.get('saleInfo', {}) or {}
                            is_ebook = bool(sale_info.get('isEbook'))
                            ebook_bonus = 1 if is_ebook else 0
                            score = size_score * 10 + ebook_bonus
                            if score > best_score:
                                best_score = score
                                best_volume = volume
                                best_thumb_url = url
                            break  # We already picked best size for this item

                    if best_volume is None:
                        # Fallback to first volume even if it has no image
                        best_volume = items[0].get('volumeInfo', {}) or {}
                        best_thumb_url = ''

                    volume = best_volume

                    # Extract subtitle if available
                    title = volume.get('title', 'Unknown')
                    subtitle = volume.get('subtitle', '')
                    full_title = f"{title}: {subtitle}" if subtitle else title

                    # Extract publication date
                    pub_date = volume.get('publishedDate', 'Unknown')

                    # Extract subjects
                    subjects = volume.get('categories', [])
                    subject = ', '.join(subjects) if subjects else 'General'

                    thumb_url = best_thumb_url

                    return {
                        'title': title,
                        'subtitle': subtitle,
                        'full_title': full_title,
                        'authors': ', '.join(volume.get('authors', ['Unknown'])),
                        'publisher': volume.get('publisher', 'Unknown'),
                        'publication_date': pub_date,
                        'category': subject,
                        'subject': subject,
                        'description': volume.get('description', '')[:200],
                        'pages': volume.get('pageCount', 0),
                        # We still call this field 'thumbnail' for compatibility,
                        # but it now points to the highest-res cover URL we could find.
                        'thumbnail': thumb_url,
                        'isbn': isbn,
                        'source': 'Google Books'
                    }
            
            return None
        
        except requests.exceptions.RequestException as e:
            print(f"Google Books API error: {e}")
            return None
        except (KeyError, IndexError, ValueError) as e:
            print(f"Error parsing Google Books response: {e}")
            return None
    
    @staticmethod
    def fetch_openlibrary(isbn: str, timeout: int = 5) -> Optional[Dict[str, Any]]:
        """
        Fetch book details from Open Library API (fallback).
        
        Args:
            isbn: ISBN-13 code
            timeout: Request timeout in seconds
        
        Returns:
            Dictionary with book details or None
        """
        try:
            params = {
                'bibkeys': f'ISBN:{isbn}',
                'jscmd': 'data',
                'format': 'json'
            }
            response = requests.get(ISBNLookup.OPENLIBRARY_URL, 
                                   params=params, timeout=timeout)
            response.raise_for_status()
            
            data = response.json()
            
            if not data:
                return None
            
            key = list(data.keys())[0]
            book_data = data[key]
            
            authors = book_data.get('authors', [{}])
            author_names = ', '.join([a.get('name', 'Unknown') for a in authors])
            
            # Extract subtitle
            subtitle = book_data.get('subtitle', '')
            
            # Extract publication date
            pub_date = book_data.get('publish_date', 'Unknown')
            
            # Extract publisher (handle dict structure)
            publishers = book_data.get('publishers', [{}])
            publisher_name = 'Unknown'
            if publishers and len(publishers) > 0:
                if isinstance(publishers[0], dict):
                    publisher_name = publishers[0].get('name', 'Unknown')
                else:
                    publisher_name = str(publishers[0])
            
            # Extract subjects (can be strings or dicts)
            subjects = book_data.get('subjects', ['General'])
            subject_names = []
            for subj in subjects[:3]:  # Take first 3 subjects
                if isinstance(subj, dict):
                    subject_names.append(subj.get('name', str(subj)))
                else:
                    subject_names.append(str(subj))
            subject = ', '.join(subject_names) if subject_names else 'General'
            
            # Build full title with subtitle
            title = book_data.get('title', 'Unknown')
            full_title = f"{title}: {subtitle}" if subtitle else title
            
            cover_info = book_data.get('cover', {}) or {}
            # Prefer large cover for better resolution
            thumb_url = (
                cover_info.get('large')
                or cover_info.get('medium')
                or cover_info.get('small')
                or ''
            )
            thumb_url = ISBNLookup._upgrade_openlibrary_thumbnail(thumb_url)
            
            return {
                'title': title,
                'subtitle': subtitle,
                'full_title': full_title,
                'authors': author_names,
                'publisher': publisher_name,
                'publication_date': pub_date,
                'category': subject,
                'subject': subject,
                'description': book_data.get('excerpts', [{}])[0].get('text', '')[:200],
                'pages': book_data.get('number_of_pages', 0),
                # Same field name, now using highest-res cover we can get
                'thumbnail': thumb_url,
                'isbn': isbn,
                'source': 'Open Library'
            }
        
        except requests.exceptions.RequestException as e:
            print(f"Open Library API error: {e}")
            return None
        except (KeyError, IndexError, ValueError) as e:
            print(f"Error parsing Open Library response: {e}")
            return None
    
    @staticmethod
    def _upgrade_openlibrary_thumbnail(url: str) -> str:
        """
        Try to upgrade an Open Library cover URL to use the large variant.
        
        Many Open Library thumbnails follow the pattern:
        ...-S.jpg, ...-M.jpg, ...-L.jpg
        If we only have S/M, we can usually get L by replacing the suffix.
        """
        if not url:
            return url
        if "covers.openlibrary.org" not in url:
            return url
        if "-L." in url or "-L.jpg" in url:
            return url
        # Replace common size suffixes with -L (handle query strings as well)
        upgraded = url.replace("-M.", "-L.").replace("-S.", "-L.")
        upgraded = upgraded.replace("-M.jpg", "-L.jpg").replace("-S.jpg", "-L.jpg")
        return upgraded

    @staticmethod
    def _upgrade_google_thumbnail(url: str) -> str:
        """
        Try to upgrade a Google Books thumbnail URL to a higher zoom level.
        
        Typical pattern:
        http(s)://books.google.com/books/content?...&zoom=1&...
        We can usually get a clearer cover by increasing zoom to 2 or 3.
        """
        if not url:
            return url
        if "books.google." not in url:
            return url
        # Only bump very low zoom values (0/1) up to 2.
        # Higher zoom levels are more likely to return placeholders / errors.
        m = re.search(r"zoom=(\d+)", url)
        if not m:
            return url
        try:
            z = int(m.group(1))
        except ValueError:
            return url
        if z >= 2:
            return url
        return re.sub(r"zoom=\d+", "zoom=2", url)
    
    @staticmethod
    def fetch_isbn(isbn: str, cache: Optional[Dict] = None) -> Optional[Dict[str, Any]]:
        """
        Fetch ISBN with fallback strategy and caching.
        
        Priority: Cache → Google Books (with retry) → Open Library → None
        
        Args:
            isbn: ISBN-13 code
            cache: Optional cache dictionary
        
        Returns:
            Dictionary with book details or None
        """
        # Check cache first
        if cache and isbn in cache:
            print(f"[Cache Hit] ISBN {isbn}")
            cached = cache[isbn]
            thumb = cached.get('thumbnail', '')
            # Upgrade both Google and Open Library thumbnails when possible
            new_thumb = ISBNLookup._upgrade_google_thumbnail(
                ISBNLookup._upgrade_openlibrary_thumbnail(thumb)
            )
            if new_thumb != thumb:
                cached['thumbnail'] = new_thumb
                cache[isbn] = cached
            return cached
        
        # Validate ISBN
        if not ISBNLookup.validate_isbn(isbn):
            print(f"Invalid ISBN format: {isbn}")
            return None
        
        # Try Google Books (with retry logic for rate limiting)
        print(f"[Fetching] Trying Google Books API for ISBN {isbn}...")
        result = ISBNLookup.fetch_google_books(isbn)
        if result:
            print(f"[Success] Found on Google Books")
            return result
        
        # If Google Books fails, try Open Library as fallback
        print(f"[Fallback] Trying Open Library API for ISBN {isbn}...")
        result = ISBNLookup.fetch_openlibrary(isbn)
        if result:
            print(f"[Success] Found on Open Library")
            return result
        
        print(f"[Failed] ISBN {isbn} not found in any database")
        return None
