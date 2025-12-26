"""Book Browser GUI Component"""

import customtkinter as ctk
from typing import Optional, Dict, Any, List, Callable
import os
import json
from pathlib import Path
from ..tools.book_retrieval_tools import get_book_metadata, search_by_author, search_by_series, search_by_genre


class BookBrowser(ctk.CTkToplevel):
    """Book browsing interface with filtering and sorting"""
    
    def __init__(self, parent, framework=None, on_book_select: Optional[Callable] = None):
        super().__init__(parent)
        
        self.framework = framework
        self.on_book_select = on_book_select
        self.books_data = []
        self.filtered_books = []
        
        self.title("Book Browser")
        self.geometry("1200x800")
        
        self._create_widgets()
        self._load_books()
    
    def _create_widgets(self):
        """Create GUI widgets"""
        # Main container
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        # Header with filters
        self.header_frame = ctk.CTkFrame(self)
        self.header_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=5)
        self.header_frame.grid_columnconfigure(3, weight=1)
        
        # Filter by author
        ctk.CTkLabel(self.header_frame, text="Author:").grid(row=0, column=0, padx=5, pady=5)
        self.author_filter = ctk.CTkEntry(self.header_frame, width=200, placeholder_text="Filter by author...")
        self.author_filter.grid(row=0, column=1, padx=5, pady=5)
        self.author_filter.bind("<KeyRelease>", lambda e: self._apply_filters())
        
        # Filter by series
        ctk.CTkLabel(self.header_frame, text="Series:").grid(row=0, column=2, padx=5, pady=5)
        self.series_filter = ctk.CTkEntry(self.header_frame, width=200, placeholder_text="Filter by series...")
        self.series_filter.grid(row=0, column=3, padx=5, pady=5)
        self.series_filter.bind("<KeyRelease>", lambda e: self._apply_filters())
        
        # Filter by genre
        ctk.CTkLabel(self.header_frame, text="Genre:").grid(row=1, column=0, padx=5, pady=5)
        self.genre_filter = ctk.CTkEntry(self.header_frame, width=200, placeholder_text="Filter by genre...")
        self.genre_filter.grid(row=1, column=1, padx=5, pady=5)
        self.genre_filter.bind("<KeyRelease>", lambda e: self._apply_filters())
        
        # Sort options
        ctk.CTkLabel(self.header_frame, text="Sort by:").grid(row=1, column=2, padx=5, pady=5)
        self.sort_option = ctk.CTkComboBox(
            self.header_frame,
            values=["Title", "Author", "Series", "Date"],
            width=150,
            command=self._apply_filters
        )
        self.sort_option.set("Title")
        self.sort_option.grid(row=1, column=3, padx=5, pady=5)
        
        # View toggle
        self.view_toggle = ctk.CTkSegmentedButton(
            self.header_frame,
            values=["List", "Grid"],
            command=self._toggle_view
        )
        self.view_toggle.set("List")
        self.view_toggle.grid(row=0, column=4, rowspan=2, padx=10, pady=5)
        
        # Main content area
        self.content_frame = ctk.CTkFrame(self)
        self.content_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        self.content_frame.grid_columnconfigure(0, weight=1)
        self.content_frame.grid_rowconfigure(0, weight=1)
        
        # Scrollable frame for books
        self.books_scroll = ctk.CTkScrollableFrame(self.content_frame)
        self.books_scroll.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.books_scroll.grid_columnconfigure(0, weight=1)
        
        # Status label
        self.status_label = ctk.CTkLabel(
            self.content_frame,
            text="Loading books...",
            font=("Arial", 12)
        )
        self.status_label.grid(row=1, column=0, pady=5)
    
    def _load_books(self):
        """Load all books from metadata directory"""
        books_metadata_dir = os.path.join(
            os.getenv("EXTRACTED_DOCS_DIR", "./data/extracted_docs"),
            "books",
            "metadata"
        )
        
        if not os.path.exists(books_metadata_dir):
            self.status_label.configure(text="No books found. Process books first.")
            return
        
        # Load all metadata files
        metadata_files = list(Path(books_metadata_dir).glob("*.json"))
        self.books_data = []
        
        for metadata_file in metadata_files:
            try:
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                    metadata['book_id'] = metadata_file.stem
                    self.books_data.append(metadata)
            except Exception as e:
                print(f"Error loading {metadata_file}: {e}")
        
        self.filtered_books = self.books_data.copy()
        self._update_display()
        self.status_label.configure(text=f"Loaded {len(self.books_data)} books")
    
    def _apply_filters(self):
        """Apply filters and sorting"""
        author_filter = self.author_filter.get().lower().strip()
        series_filter = self.series_filter.get().lower().strip()
        genre_filter = self.genre_filter.get().lower().strip()
        sort_by = self.sort_option.get()
        
        # Filter
        self.filtered_books = []
        for book in self.books_data:
            author = book.get('author', '').lower()
            series = book.get('series', '').lower()
            genres = [g.lower() for g in book.get('genre', [])]
            
            if author_filter and author_filter not in author:
                continue
            if series_filter and series_filter not in series:
                continue
            if genre_filter and not any(genre_filter in g for g in genres):
                continue
            
            self.filtered_books.append(book)
        
        # Sort
        if sort_by == "Title":
            self.filtered_books.sort(key=lambda x: x.get('title', '').lower())
        elif sort_by == "Author":
            self.filtered_books.sort(key=lambda x: x.get('author', '').lower())
        elif sort_by == "Series":
            self.filtered_books.sort(key=lambda x: (x.get('series', '').lower(), x.get('series_number', 0)))
        elif sort_by == "Date":
            self.filtered_books.sort(key=lambda x: x.get('publication_date', ''), reverse=True)
        
        self._update_display()
        self.status_label.configure(text=f"Showing {len(self.filtered_books)} of {len(self.books_data)} books")
    
    def _update_display(self):
        """Update book display"""
        # Clear existing
        for widget in self.books_scroll.winfo_children():
            widget.destroy()
        
        view_mode = self.view_toggle.get()
        
        if view_mode == "List":
            self._display_list_view()
        else:
            self._display_grid_view()
    
    def _display_list_view(self):
        """Display books in list view"""
        for i, book in enumerate(self.filtered_books):
            book_frame = ctk.CTkFrame(self.books_scroll)
            book_frame.grid(row=i, column=0, sticky="ew", padx=5, pady=5)
            book_frame.grid_columnconfigure(1, weight=1)
            
            # Title
            title_label = ctk.CTkLabel(
                book_frame,
                text=book.get('title', 'Unknown Title'),
                font=("Arial", 14, "bold"),
                anchor="w"
            )
            title_label.grid(row=0, column=0, columnspan=2, padx=10, pady=5, sticky="w")
            
            # Author
            author_text = f"by {book.get('author', 'Unknown Author')}"
            if book.get('series'):
                author_text += f" | {book.get('series')}"
                if book.get('series_number'):
                    author_text += f" #{book.get('series_number')}"
            
            author_label = ctk.CTkLabel(
                book_frame,
                text=author_text,
                font=("Arial", 11),
                anchor="w"
            )
            author_label.grid(row=1, column=0, padx=10, pady=2, sticky="w")
            
            # Open button
            open_btn = ctk.CTkButton(
                book_frame,
                text="Open",
                command=lambda b=book: self._open_book(b),
                width=80
            )
            open_btn.grid(row=0, column=2, rowspan=2, padx=10, pady=5)
    
    def _display_grid_view(self):
        """Display books in grid view"""
        cols = 3
        for i, book in enumerate(self.filtered_books):
            row = i // cols
            col = i % cols
            
            book_frame = ctk.CTkFrame(self.books_scroll, width=300, height=200)
            book_frame.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
            
            # Title
            title_label = ctk.CTkLabel(
                book_frame,
                text=book.get('title', 'Unknown Title'),
                font=("Arial", 12, "bold"),
                wraplength=250
            )
            title_label.pack(pady=10)
            
            # Author
            author_label = ctk.CTkLabel(
                book_frame,
                text=book.get('author', 'Unknown Author'),
                font=("Arial", 10)
            )
            author_label.pack(pady=5)
            
            # Open button
            open_btn = ctk.CTkButton(
                book_frame,
                text="Open",
                command=lambda b=book: self._open_book(b),
                width=100
            )
            open_btn.pack(pady=10)
    
    def _toggle_view(self, value: str):
        """Toggle between list and grid view"""
        self._update_display()
    
    def _open_book(self, book: Dict):
        """Open book in reader"""
        book_id = book.get('book_id')
        if book_id and self.on_book_select:
            self.on_book_select(book_id)
        elif book_id:
            # Open in new reader window
            from .book_reader import BookReader
            reader = BookReader(self, self.framework, book_id)

