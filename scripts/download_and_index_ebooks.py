"""Download ebooks and index them for chatbot"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.extractors.ebooks.ebook_downloader import EbookDownloader
from src.bmad.framework import BMADFramework
from src.agents import DocumentAgent, RetrievalAgent
from dotenv import load_dotenv
import os

load_dotenv()

def main():
    print("=" * 70)
    print("EBOOK DOWNLOAD AND INDEXING")
    print("=" * 70)
    print()
    
    # Download and extract ebooks
    downloader = EbookDownloader()
    md_file = downloader.extract()
    
    if not md_file:
        print("⚠️  No ebooks extracted")
        return
    
    print()
    print("=" * 70)
    print("INDEXING EBOOKS")
    print("=" * 70)
    print()
    
    # Index the markdown file
    memory_path = os.getenv("CHAT_HISTORY_DIR", "./data/chat_history")
    framework = BMADFramework(memory_storage_path=memory_path)
    
    document_agent = DocumentAgent(framework=framework)
    retrieval_agent = RetrievalAgent(framework=framework)
    framework.register_agent(document_agent)
    framework.register_agent(retrieval_agent)
    
    print(f"  Processing {md_file.name}...")
    
    try:
        result = document_agent.process({"file_paths": [str(md_file)]})
        chunks = result.get("chunks", [])
        
        if chunks:
            print(f"  ✓ Created {len(chunks)} chunks")
            print(f"  Indexing chunks...")
            retrieval_agent.index_chunks(chunks)
            print(f"  ✓ Indexed {len(chunks)} chunks")
        else:
            print("  ⚠️  No chunks created")
    except Exception as e:
        print(f"  ⚠️  Error: {e}")
        import traceback
        traceback.print_exc()
    
    print()
    print("=" * 70)
    print("COMPLETE!")
    print("=" * 70)
    print()
    print("Ebooks are now available for the chatbot to reference!")
    print(f"Markdown file: {md_file}")

if __name__ == "__main__":
    main()

