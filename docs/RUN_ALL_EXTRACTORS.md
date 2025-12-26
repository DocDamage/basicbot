# How to Run All Database Extractors

## Quick Start

```bash
python extract_and_index_all_databases.py
```

This will extract and index all 16 databases automatically.

## Individual Testing

Test each extractor individually:

```python
# TSCA
from src.extractors.chemical_compliance.tsca_chemical_inventory_extractor import TSCAChemicalInventoryExtractor
extractor = TSCAChemicalInventoryExtractor()
md_file = extractor.extract()

# RoHS
from src.extractors.chemical_compliance.rohs_database_extractor import RoHSDatabaseExtractor
extractor = RoHSDatabaseExtractor()
md_file = extractor.extract()

# FDA Orange Book
from src.extractors.healthcare.fda_orange_book_extractor import FDAOrangeBookExtractor
extractor = FDAOrangeBookExtractor()
md_file = extractor.extract()

# And so on for all 16 databases...
```

## What Happens

1. **Download**: Each extractor downloads raw data from its source
2. **Parse**: Data is parsed into structured format
3. **Convert**: Data is converted to markdown with metadata
4. **Save**: Markdown files saved to `data/extracted_docs/compliance/[db_name]/md/`
5. **Index**: All markdown files are indexed in vector database
6. **Query**: Data becomes searchable in your chatbot

## Expected Output

- Raw data files in: `data/extracted_docs/compliance/[db_name]/raw/`
- Markdown files in: `data/extracted_docs/compliance/[db_name]/md/`
- Indexed in: Vector database (Qdrant)

## Troubleshooting

- **403 Errors**: Some sites block automated scraping - manual download may be needed
- **No Data**: Check if website structure changed - may need to update extractor
- **Large Files**: Some databases are very large - extraction may take time
- **API Keys**: Some databases require API keys - check individual documentation

## Next Steps After Extraction

1. Verify markdown files were created
2. Check data quality
3. Test queries in chatbot
4. Add specialized search tools if needed

