# Backend Scripts

Backend scripts for ebook ingestion and processing.

## ebook_ingest.py

Main script for ingesting ebooks from the `books/` folder into the database.

### Usage

```bash
# Basic usage (processes books/ folder recursively and indexes)
python backend/ebook_ingest.py

# Specify custom books directory
python backend/ebook_ingest.py --books-dir /path/to/books

# Process without recursion (only top-level files)
python backend/ebook_ingest.py --no-recursive

# Process but don't index in vector database
python backend/ebook_ingest.py --no-index

# Combine options
python backend/ebook_ingest.py --books-dir ./my_books --no-index
```

### Options

- `--books-dir`: Directory containing books (default: `./books` or `BOOKS_DIR` env var)
- `--no-recursive`: Only process files in the top-level directory, not subdirectories
- `--no-index`: Process books but don't index them in the vector database

### What it does

1. **Processes books**: Extracts content and metadata from PDF, EPUB, MOBI, and TXT files
2. **Extracts entities**: Identifies characters, locations, and key entities using NER
3. **Detects duplicates**: Finds and merges duplicate books across formats
4. **Chunks content**: Creates searchable chunks with chapter-based hybrid chunking
5. **Indexes in vector DB**: Stores chunks in Qdrant for semantic search
6. **Logs progress**: Creates detailed logs in `data/logs/ebook_ingest_*.log`

### Output

- Processed books stored in: `data/extracted_docs/books/`
- Metadata files: `data/extracted_docs/books/metadata/`
- Processed markdown: `data/extracted_docs/books/processed/`
- Entity index: `data/extracted_docs/books/entities/`
- Vector database: `data/vector_db/` (or Qdrant server)

### Environment Variables

- `BOOKS_DIR`: Default books directory (default: `./books`)
- `EXTRACTED_DOCS_DIR`: Directory for processed files (default: `./data/extracted_docs`)
- `CHAT_HISTORY_DIR`: Directory for chat history (default: `./data/chat_history`)
- `QDRANT_HOST`: Qdrant server host (default: `localhost`)
- `QDRANT_PORT`: Qdrant server port (default: `6333`)

### Notes

- The script uses the BMAD framework and BookAgent for processing
- Books are automatically archived after processing (moved to `books/.archive/`)
- The script can be run multiple times - it will skip already processed books
- Large files (>10MB) are automatically skipped to prevent freezing

### Python 3.13 Compatibility

This script includes compatibility fixes for Python 3.13, which removed the `six.moves` module.
The compatibility shim is automatically loaded from `src/utils/six_moves_compat.py`.

If you encounter import errors related to `six.moves`, ensure that:
1. The compatibility module is properly imported (it should be automatic)
2. All dependencies are up to date: `pip install -r requirements.txt`
3. If issues persist, consider using Python 3.12 or earlier

