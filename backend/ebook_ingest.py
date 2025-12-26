import os
import sqlite3
import uuid
import shutil
import re
from datetime import datetime
import hashlib
from io import BytesIO

# Optional/Lazy Imports
pytesseract = None
convert_from_path = None
ebooklib = None
epub = None
BeautifulSoup = None
requests = None

try:
    import pytesseract
    from pdf2image import convert_from_path
except ImportError:
    pass
    
try:
    import ebooklib
    from ebooklib import epub
    from bs4 import BeautifulSoup
except ImportError:
    pass

# Configuration
LIBRARY_ROOT = r"C:\Users\dferr\Desktop\dareaschatbot\library\books\books"
DB_PATH = "backend/library.db"
RAG_DATA_PATH = "backend/rag_data/library_imports"

# Setup Tesseract (User must verify path)
# Common default paths
tesseract_paths = [
    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    r"C:\Users\dferr\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"
]
for path in tesseract_paths:
    if os.path.exists(path):
        pytesseract.pytesseract.tesseract_cmd = path
        break

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def normalize_text(text):
    if not text: return ""
    return re.sub(r'\s+', ' ', text).strip().lower()

def generate_book_id(title, author):
    # Deterministic ID based on Title+Author
    raw = f"{normalize_text(title)}_{normalize_text(author)}"
    return hashlib.md5(raw.encode()).hexdigest()

def extract_epub_metadata(path):
    try:
        book = epub.read_epub(path)
        title = book.get_metadata('DC', 'title')[0][0]
        try:
            author = book.get_metadata('DC', 'creator')[0][0]
        except:
            author = "Unknown Author"
        return title, author
    except Exception as e:
        print(f"EPUB Metadata Error ({path}): {e}")
        return os.path.basename(path), "Unknown"

def extract_pdf_metadata(path):
    # PDFs are notorious for bad metadata, rely on filename as primary
    filename = os.path.splitext(os.path.basename(path))[0]
    # Simple heuristic: "Title - Author" or "Author - Title"
    parts = filename.split(" - ")
    if len(parts) >= 2:
        return parts[1], parts[0] # Assume Author - Title usually
    return filename, "Unknown"

def extract_text_from_pdf(path, use_ocr=True):
    # Placeholder for full PDF extraction logic
    # Realistically, for huge files, we stream this.
    try:
        from pypdf import PdfReader
        reader = PdfReader(path)
        text = ""
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text and len(page_text.strip()) > 50:
                text += page_text + "\n"
            elif use_ocr:
                # Fallback to OCR for this page - unimplemented in MVP due to speed
                # We will mark it as "Scanned"
                pass
        return text
    except:
        return ""

def download_cover(title, author):
    import requests  # Import inside function to avoid lazy import issues
    print(f"Searching cover for: {title} by {author}...")
    try:
        # OpenLibrary Search
        q = f"{title} {author}".replace(" ", "+")
        url = f"https://openlibrary.org/search.json?q={q}"
        res = requests.get(url, timeout=5)
        if res.status_code == 200:
            data = res.json()
            if data['numFound'] > 0:
                doc = data['docs'][0]
                if 'cover_i' in doc:
                    cover_id = doc['cover_i']
                    cover_url = f"https://covers.openlibrary.org/b/id/{cover_id}-L.jpg"
                    img_data = requests.get(cover_url).content
                    return img_data
    except Exception as e:
        print(f"Cover download failed: {e}")
    return None

def process_file(path):
    ext = os.path.splitext(path)[1].lower()
    if ext not in ['.epub', '.pdf', '.mobi', '.txt']:
        return

    print(f"Processing: {os.path.basename(path)}")
    
    if ext == '.epub':
        title, author = extract_epub_metadata(path)
    else:
        title, author = extract_pdf_metadata(path)
        
    book_id = generate_book_id(title, author)
    
    conn = None
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # check if book exists
        cursor.execute("SELECT id FROM books WHERE id = ?", (book_id,))
        if not cursor.fetchone():
            # New Book
            print(f"New Book Found: {title}")
            cover_blob = download_cover(title, author)
            cover_path = ""
            if cover_blob:
                cover_filename = f"{book_id}.jpg"
                cover_full_path = os.path.join("frontend/public/covers", cover_filename)
                os.makedirs(os.path.dirname(cover_full_path), exist_ok=True)
                with open(cover_full_path, "wb") as f:
                    f.write(cover_blob)
                cover_path = f"/covers/{cover_filename}"
                
            cursor.execute("INSERT INTO books (id, title, author, cover_image_path) VALUES (?, ?, ?, ?)",
                          (book_id, title, author, cover_path))
        
        # Add File Entry
        cursor.execute("INSERT OR IGNORE INTO book_files (book_id, file_path, format) VALUES (?, ?, ?)",
                      (book_id, path, ext.replace('.', '')))
        
        conn.commit()
    except Exception as e:
        print(f"Error processing {path}: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

def scan_library():
    if not os.path.exists(LIBRARY_ROOT):
        os.makedirs(LIBRARY_ROOT)
        print(f"Created {LIBRARY_ROOT}. Drop files here!")
        return

    print("Scanning library...")
    for root, dirs, files in os.walk(LIBRARY_ROOT):
        for file in files:
            process_file(os.path.join(root, file))
    print("Scan complete.")

if __name__ == "__main__":
    scan_library()
