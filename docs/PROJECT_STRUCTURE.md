# Project Structure

This document describes the organization of files and folders in the project.

## Directory Structure

```
basicbot/
├── README.md                    # Main project README
├── requirements.txt             # Python dependencies
├── process_books.py             # Main entry point for book processing
│
├── src/                         # Source code
│   ├── agents/                  # BMAD framework agents
│   ├── bmad/                    # BMAD framework core
│   ├── config/                  # Configuration files
│   ├── extractors/              # Data extractors
│   ├── gui/                     # GUI components
│   ├── tools/                   # Utility tools
│   └── main.py                  # Application entry point
│
├── docs/                        # Documentation files
│   ├── *.md                     # Markdown documentation
│   └── *.json                   # JSON documentation/config
│
├── scripts/                     # Utility scripts
│   ├── *.py                     # Python utility scripts
│   └── *.bat                    # Batch scripts
│
├── data/                        # Data storage
│   ├── archives/                # ZIP and PDF archives
│   ├── plans/                   # Integration plans
│   ├── extracted_docs/          # Extracted documents
│   ├── vector_db/               # Vector database files
│   ├── chat_history/            # Chat history
│   └── logs/                    # Log files
│
└── books/                       # Book collection
    └── [book folders]           # Organized by author/series
```

## File Organization

### Documentation (`docs/`)
- All `.md` files (except README.md in root)
- All `.json` plan files
- Integration plans moved to `data/plans/`

### Scripts (`scripts/`)
- Utility Python scripts (`.py`)
- Batch scripts (`.bat`)
- Note: Main entry points (`process_books.py`, `src/main.py`) remain in root/src

### Archives (`data/archives/`)
- ZIP files
- PDF files (except those in `books/` folder)

### Plans (`data/plans/`)
- Integration plan files
- Database integration plans

### Source Code (`src/`)
- `agents/` - BMAD framework agents
- `bmad/` - BMAD framework core
- `config/` - Configuration management
- `extractors/` - Data extraction modules
- `gui/` - GUI components (CustomTkinter)
- `tools/` - Utility tools and helpers
- `main.py` - Application entry point

## Key Files

### Main Entry Points
- `process_books.py` - Process books from books/ folder
- `src/main.py` - Main application entry point

### Configuration
- `requirements.txt` - Python dependencies
- `data/config.json` - Application settings
- `src/config/settings.py` - Settings management

### Documentation
- `README.md` - Project overview
- `docs/` - All documentation files

