"""Verify ebook ingestion results"""

import os
import json
from pathlib import Path

print("=" * 70)
print("EBOOK INGESTION VERIFICATION REPORT")
print("=" * 70)
print()

# Check metadata files
metadata_dir = Path("data/extracted_docs/books/metadata")
if metadata_dir.exists():
    metadata_files = list(metadata_dir.glob("*.json"))
    print(f"✓ Metadata files: {len(metadata_files):,}")
    
    # Sample a few and get stats
    sample_count = min(5, len(metadata_files))
    total_chapters = 0
    total_characters = 0
    total_words = 0
    authors = set()
    genres = set()
    
    print(f"\nAnalyzing {sample_count} sample books...")
    for f in metadata_files[:sample_count]:
        try:
            with open(f, 'r', encoding='utf-8') as file:
                data = json.load(file)
                title = data.get('title', 'Unknown')
                author = data.get('author', 'Unknown')
                chapters = data.get('chapters', [])
                characters = data.get('characters', [])
                word_count = data.get('word_count', 0)
                
                total_chapters += len(chapters)
                total_characters += len(characters)
                total_words += word_count
                if author:
                    authors.add(author)
                if data.get('genre'):
                    genres.update(data.get('genre', []))
                
                print(f"  - {title[:60]} by {author[:30]}")
                print(f"    Chapters: {len(chapters)}, Characters: {len(characters)}, Words: {word_count:,}")
        except Exception as e:
            print(f"  - Error reading {f.name}: {e}")
    
    print(f"\nSample Statistics:")
    print(f"  Average chapters per book: {total_chapters / sample_count:.1f}")
    print(f"  Average characters per book: {total_characters / sample_count:.1f}")
    print(f"  Average words per book: {total_words / sample_count:,.0f}")
    print(f"  Unique authors in sample: {len(authors)}")
else:
    print("✗ Metadata directory not found")

print()

# Check processed files
processed_dir = Path("data/extracted_docs/books/processed")
if processed_dir.exists():
    processed_files = list(processed_dir.glob("*.md"))
    print(f"✓ Processed markdown files: {len(processed_files):,}")
    if processed_files:
        total_size = sum(f.stat().st_size for f in processed_files)
        avg_size = total_size / len(processed_files)
        print(f"  Total size: {total_size / (1024*1024):.2f} MB")
        print(f"  Average file size: {avg_size / 1024:.2f} KB")
        
        # Check a sample file
        sample_file = processed_files[0]
        with open(sample_file, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = len(content.split('\n'))
            words = len(content.split())
            print(f"\n  Sample file ({sample_file.name}):")
            print(f"    Lines: {lines:,}, Words: {words:,}")
else:
    print("✗ Processed directory not found")

print()

# Check entity index
entity_index = Path("data/extracted_docs/books/entities/entity_index.json")
if entity_index.exists():
    try:
        with open(entity_index, 'r', encoding='utf-8') as f:
            entities = json.load(f)
            total_entities = sum(len(v) if isinstance(v, list) else 1 for v in entities.values())
            print(f"✓ Entity index found")
            print(f"  Entity types: {len(entities)}")
            print(f"  Total entities: {total_entities:,}")
            print(f"  Books indexed: {entities.get('total_books', 0):,}")
    except Exception as e:
        print(f"✗ Error reading entity index: {e}")
else:
    print("✗ Entity index not found")

print()

# Summary
print("=" * 70)
print("SUMMARY")
print("=" * 70)
print(f"✓ Books processed: {len(metadata_files) if metadata_dir.exists() else 0:,}")
print(f"✓ Markdown files created: {len(processed_files) if processed_dir.exists() else 0:,}")
print(f"✓ Entity extraction: {'Complete' if entity_index.exists() else 'Not found'}")
print()
print("Note: Vector database indexing status needs to be checked separately.")
print("If you ran with --no-index, books were processed but not indexed.")
print("Run without --no-index to index books in the vector database.")
print("=" * 70)

