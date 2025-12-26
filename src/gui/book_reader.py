"""Book Reader GUI Component"""

import customtkinter as ctk
from typing import Optional, Dict, Any, Callable, List
import os
import json
import logging
from pathlib import Path
from ..tools.book_retrieval_tools import get_full_book_text, get_book_metadata
from ..config import get_settings

logger = logging.getLogger('book_reader')


class BookReader(ctk.CTkToplevel):
    """Book reading window with pagination and navigation"""
    
    def __init__(self, parent, framework=None, book_id: Optional[str] = None):
        super().__init__(parent)
        
        self.framework = framework
        self.book_id = book_id
        self.book_text = ""
        self.book_metadata = {}
        self.current_page = 0
        self.settings = get_settings()
        # Get configurable words per page (default 500)
        self.words_per_page = self.settings.get("book_reader.words_per_page", 500)
        self.pages = []
        self.bookmarks: List[Dict[str, Any]] = []
        self.bookmarks_file = self._get_bookmarks_file()
        self._load_bookmarks()
        
        self.title("Book Reader")
        self.geometry("1000x700")
        
        self._create_widgets()
        
        if book_id:
            self.load_book(book_id)
    
    def _create_widgets(self):
        """Create GUI widgets"""
        # Main container
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        # Header with book info
        self.header_frame = ctk.CTkFrame(self)
        self.header_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=5)
        self.header_frame.grid_columnconfigure(1, weight=1)
        
        self.title_label = ctk.CTkLabel(
            self.header_frame,
            text="No book loaded",
            font=("Arial", 16, "bold")
        )
        self.title_label.grid(row=0, column=0, columnspan=2, padx=10, pady=5, sticky="w")
        
        self.author_label = ctk.CTkLabel(
            self.header_frame,
            text="",
            font=("Arial", 12)
        )
        self.author_label.grid(row=1, column=0, padx=10, pady=2, sticky="w")
        
        # Navigation buttons
        self.nav_frame = ctk.CTkFrame(self.header_frame)
        self.nav_frame.grid(row=0, column=2, rowspan=2, padx=10, pady=5)
        
        self.prev_btn = ctk.CTkButton(
            self.nav_frame,
            text="◀ Prev",
            command=self._prev_page,
            width=80
        )
        self.prev_btn.pack(side="left", padx=5)
        
        self.page_label = ctk.CTkLabel(
            self.nav_frame,
            text="Page 0 / 0",
            width=100
        )
        self.page_label.pack(side="left", padx=5)
        
        self.next_btn = ctk.CTkButton(
            self.nav_frame,
            text="Next ▶",
            command=self._next_page,
            width=80
        )
        self.next_btn.pack(side="left", padx=5)
        
        # Main content area
        self.content_frame = ctk.CTkFrame(self)
        self.content_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        self.content_frame.grid_columnconfigure(0, weight=1)
        self.content_frame.grid_rowconfigure(0, weight=1)
        
        # Text display with scrollbar
        self.text_display = ctk.CTkTextbox(
            self.content_frame,
            wrap="word",
            font=("Arial", 12),
            width=900
        )
        self.text_display.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        
        # Sidebar with chapters and bookmarks
        self.sidebar = ctk.CTkFrame(self.content_frame, width=200)
        self.sidebar.grid(row=0, column=1, sticky="nsew", padx=(0, 10), pady=10)
        
        # Chapter navigation
        ctk.CTkLabel(
            self.sidebar,
            text="Chapters",
            font=("Arial", 14, "bold")
        ).pack(pady=10)
        
        self.chapter_listbox = ctk.CTkScrollableFrame(self.sidebar, height=200)
        self.chapter_listbox.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Bookmarks
        ctk.CTkLabel(
            self.sidebar,
            text="Bookmarks",
            font=("Arial", 14, "bold")
        ).pack(pady=10)
        
        self.bookmark_btn = ctk.CTkButton(
            self.sidebar,
            text="Add Bookmark",
            command=self._add_bookmark,
            width=150
        )
        self.bookmark_btn.pack(pady=5)
        
        self.bookmark_listbox = ctk.CTkScrollableFrame(self.sidebar, height=150)
        self.bookmark_listbox.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Footer with search
        self.footer_frame = ctk.CTkFrame(self)
        self.footer_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=5)
        self.footer_frame.grid_columnconfigure(0, weight=1)
        
        self.search_entry = ctk.CTkEntry(
            self.footer_frame,
            placeholder_text="Search in book...",
            width=300
        )
        self.search_entry.pack(side="left", padx=10, pady=5)
        self.search_entry.bind("<Return>", lambda e: self._search_in_book())
        
        self.search_btn = ctk.CTkButton(
            self.footer_frame,
            text="Search",
            command=self._search_in_book,
            width=80
        )
        self.search_btn.pack(side="left", padx=5)
    
    def load_book(self, book_id: str) -> None:
        """
        Load book by ID
        
        Args:
            book_id: Book ID to load
        """
        self.book_id = book_id
        self.book_text = get_full_book_text(book_id)
        self.book_metadata = get_book_metadata(book_id) or {}
        
        # Update bookmarks file path for this book
        self.bookmarks_file = self._get_bookmarks_file()
        self._load_bookmarks()
        
        if not self.book_text:
            self.text_display.insert("1.0", "Error: Could not load book text.")
            logger.error(f"Could not load book text for {book_id}")
            return
        
        # Update header
        title = self.book_metadata.get('title', 'Unknown Title')
        author = self.book_metadata.get('author', 'Unknown Author')
        self.title_label.configure(text=title)
        self.author_label.configure(text=f"by {author}")
        self.title(f"Book Reader - {title}")
        
        # Split into pages
        self._split_into_pages()
        
        # Load chapters
        self._load_chapters()
        
        # Display first page
        self.current_page = 0
        self._display_page()
    
    def _split_into_pages(self) -> None:
        """
        Split book text into pages based on configured words per page
        
        Pages are split by word count to maintain readability
        """
        words = self.book_text.split()
        self.pages = []
        
        for i in range(0, len(words), self.words_per_page):
            page_words = words[i:i + self.words_per_page]
            self.pages.append(' '.join(page_words))
        
        self.page_label.configure(text=f"Page {self.current_page + 1} / {len(self.pages)}")
    
    def _display_page(self) -> None:
        """
        Display current page in text display
        
        Updates page label and navigation button states
        """
        if 0 <= self.current_page < len(self.pages):
            self.text_display.delete("1.0", "end")
            self.text_display.insert("1.0", self.pages[self.current_page])
            self.page_label.configure(text=f"Page {self.current_page + 1} / {len(self.pages)}")
            self.prev_btn.configure(state="normal" if self.current_page > 0 else "disabled")
            self.next_btn.configure(state="normal" if self.current_page < len(self.pages) - 1 else "disabled")
    
    def _prev_page(self):
        """Go to previous page"""
        if self.current_page > 0:
            self.current_page -= 1
            self._display_page()
    
    def _next_page(self):
        """Go to next page"""
        if self.current_page < len(self.pages) - 1:
            self.current_page += 1
            self._display_page()
    
    def _load_chapters(self):
        """Load chapter navigation"""
        # Clear existing
        for widget in self.chapter_listbox.winfo_children():
            widget.destroy()
        
        chapters = self.book_metadata.get('chapters', [])
        for chapter in chapters:
            chapter_title = chapter.get('chapter_title', f"Chapter {chapter.get('chapter_number', '')}")
            btn = ctk.CTkButton(
                self.chapter_listbox,
                text=chapter_title,
                command=lambda c=chapter: self._go_to_chapter(c),
                anchor="w",
                width=180
            )
            btn.pack(pady=2, padx=5, fill="x")
    
    def _get_bookmarks_file(self) -> str:
        """Get bookmarks file path for current book"""
        if not self.book_id:
            return ""
        bookmarks_dir = os.path.join(
            os.getenv("EXTRACTED_DOCS_DIR", "./data/extracted_docs"),
            "books",
            "bookmarks"
        )
        os.makedirs(bookmarks_dir, exist_ok=True)
        return os.path.join(bookmarks_dir, f"{self.book_id}.json")
    
    def _load_bookmarks(self):
        """Load bookmarks from file"""
        if not self.bookmarks_file or not os.path.exists(self.bookmarks_file):
            return
        
        try:
            with open(self.bookmarks_file, 'r', encoding='utf-8') as f:
                self.bookmarks = json.load(f)
            self._update_bookmarks()
        except Exception as e:
            logger.error(f"Error loading bookmarks: {e}", exc_info=True)
            self.bookmarks = []
    
    def _save_bookmarks(self):
        """Save bookmarks to file"""
        if not self.bookmarks_file:
            return
        
        try:
            with open(self.bookmarks_file, 'w', encoding='utf-8') as f:
                json.dump(self.bookmarks, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving bookmarks: {e}", exc_info=True)
    
    def _go_to_chapter(self, chapter: Dict):
        """Navigate to a specific chapter using exact position"""
        # Get exact chapter start position from metadata
        chapter_start_line = chapter.get('start_line', 0)
        
        if not self.book_text or chapter_start_line == 0:
            # Fallback to estimation if no exact position
            estimated_page = chapter_start_line // (self.words_per_page // 50)
            self.current_page = max(0, min(estimated_page, len(self.pages) - 1))
        else:
            # Use exact position: find which page contains the chapter start
            lines = self.book_text.split('\n')
            if chapter_start_line < len(lines):
                # Count words up to chapter start
                words_before_chapter = len(' '.join(lines[:chapter_start_line]).split())
                # Calculate which page this corresponds to
                exact_page = words_before_chapter // self.words_per_page
                self.current_page = max(0, min(exact_page, len(self.pages) - 1))
            else:
                # Fallback
                self.current_page = 0
        
        self._display_page()
    
    def _add_bookmark(self) -> None:
        """
        Add bookmark at current page and save to file
        
        Bookmarks are persisted to JSON file for this book
        """
        if not self.pages or self.current_page >= len(self.pages):
            logger.warning("Cannot add bookmark: no pages available")
            return
        
        from datetime import datetime
        bookmark = {
            'page': self.current_page + 1,
            'text': self.pages[self.current_page][:50] + "...",
            'timestamp': datetime.now().isoformat()
        }
        self.bookmarks.append(bookmark)
        self._update_bookmarks()
        self._save_bookmarks()
        logger.debug(f"Added bookmark at page {bookmark['page']}")
    
    def _update_bookmarks(self) -> None:
        """
        Update bookmark list display in sidebar
        
        Clears existing bookmark widgets and recreates them from current bookmarks list
        """
        for widget in self.bookmark_listbox.winfo_children():
            widget.destroy()
        
        for i, bookmark in enumerate(self.bookmarks):
            btn = ctk.CTkButton(
                self.bookmark_listbox,
                text=f"Page {bookmark['page']}: {bookmark['text']}",
                command=lambda p=bookmark['page'] - 1: self._go_to_bookmark(p),
                anchor="w",
                width=180,
                height=30
            )
            btn.pack(pady=2, padx=5, fill="x")
    
    def _go_to_bookmark(self, page: int) -> None:
        """
        Navigate to a bookmarked page
        
        Args:
            page: Page number (0-indexed) to navigate to
        """
        if 0 <= page < len(self.pages):
            self.current_page = page
            self._display_page()
        else:
            logger.warning(f"Invalid bookmark page: {page}")
    
    def _search_in_book(self):
        """Search for text in book with highlighting"""
        query = self.search_entry.get().strip()
        if not query:
            return
        
        query_lower = query.lower()
        found_pages = []
        
        # Find all occurrences
        for i, page in enumerate(self.pages):
            if query_lower in page.lower():
                found_pages.append(i)
        
        if not found_pages:
            self.status_label.configure(text="No matches found")
            return
        
        # Go to first occurrence
        self.current_page = found_pages[0]
        self._display_page()
        
        # Highlight all occurrences in current page
        self._highlight_search_term(query)
        
        # Show count
        if len(found_pages) > 1:
            self.status_label.configure(text=f"Found {len(found_pages)} pages with matches (showing first)")
        else:
            self.status_label.configure(text="Found 1 match")
    
    def _highlight_search_term(self, term: str):
        """Highlight search term in text display"""
        content = self.text_display.get("1.0", "end-1c")
        term_lower = term.lower()
        content_lower = content.lower()
        
        # Remove previous highlights
        self.text_display.tag_delete("search_highlight")
        
        # Find and highlight all occurrences
        start = 0
        while True:
            pos = content_lower.find(term_lower, start)
            if pos == -1:
                break
            
            # Convert character position to line.column
            line_start = content[:pos].rfind('\n') + 1
            line_num = content[:pos].count('\n') + 1
            col_num = pos - line_start
            
            start_pos = f"{line_num}.{col_num}"
            end_pos = f"{line_num}.{col_num + len(term)}"
            
            self.text_display.tag_add("search_highlight", start_pos, end_pos)
            start = pos + 1
        
        # Configure highlight style
        self.text_display.tag_config("search_highlight", background="yellow", foreground="black")

