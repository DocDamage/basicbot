"""Master orchestrator for all database extractions"""

import sys
from pathlib import Path
import json
from typing import List, Dict

sys.path.insert(0, str(Path(__file__).parent))

from src.bmad.framework import BMADFramework
from src.agents import DocumentAgent, RetrievalAgent
from dotenv import load_dotenv
import os

load_dotenv()

def extract_all_databases():
    """Extract all databases"""
    print("=" * 70)
    print("EXTRACTING ALL DATABASES")
    print("=" * 70)
    print()
    
    # Load plan
    with open("DATABASE_INTEGRATION_PLAN.json", 'r') as f:
        plan = json.load(f)
    
    all_dbs = plan['high_priority'] + plan['medium_priority'] + plan['low_priority']
    
    extracted_files = []
    
    # Import and run extractors
    for priority in ['high', 'medium', 'low']:
        dbs = plan[f'{priority}_priority']
        print(f"{priority.upper()} PRIORITY DATABASES")
        print("-" * 70)
        
        for db in dbs:
            try:
                # Map database name to extractor file
                extractor_name = db['name'].replace(' ', '_').replace('-', '_').lower()
                category = db['category']
                file_name = f"{extractor_name}_extractor"
                
                # Try to import extractor
                try:
                    module_name = f"src.extractors.{category}.{file_name}"
                    
                    # Import the module
                    import importlib
                    module = importlib.import_module(module_name)
                    
                    # Find the extractor class (it should be the only class ending in Extractor)
                    extractor_class = None
                    for attr_name in dir(module):
                        if attr_name.endswith('Extractor') and not attr_name.startswith('_') and attr_name != 'BaseExtractor':
                            extractor_class = getattr(module, attr_name)
                            # Verify it's not the base class
                            if hasattr(extractor_class, '__module__') and 'base_extractor' not in extractor_class.__module__:
                                break
                    
                    if not extractor_class:
                        raise AttributeError(f"No Extractor class found in {module_name}")
                    
                    # Run extractor
                    extractor = extractor_class()
                    md_file = extractor.extract()
                    
                    if md_file and Path(md_file).exists():
                        extracted_files.append(Path(md_file))
                        print(f"    ✓ Successfully extracted {db['name']}")
                    else:
                        print(f"    ⚠️  Extraction returned no file for {db['name']}")
                        
                except (ImportError, AttributeError) as e:
                    print(f"  ⚠️  {db['name']}: Extractor import error")
                    print(f"     Error: {e}")
                    print(f"     Module: src.extractors.{category}.{file_name}")
            except Exception as e:
                import traceback
                error_msg = str(e)
                tb_lines = traceback.format_exc().split('\n')
                last_error = [line for line in tb_lines if 'Error' in line or 'Exception' in line or 'raise' in line][-3:] if tb_lines else []
                print(f"  ⚠️  Error processing {db['name']}: {error_msg}")
                if last_error:
                    print(f"     {' | '.join(last_error)}")
        
        print()
    
    return extracted_files

def index_extracted_files(files: List[Path]):
    """Index extracted markdown files"""
    if not files:
        print("No files to index")
        return
    
    print("=" * 70)
    print("INDEXING EXTRACTED FILES")
    print("=" * 70)
    print()
    
    memory_path = os.getenv("CHAT_HISTORY_DIR", "./data/chat_history")
    framework = BMADFramework(memory_storage_path=memory_path)
    
    document_agent = DocumentAgent(framework=framework)
    retrieval_agent = RetrievalAgent(framework=framework)
    framework.register_agent(document_agent)
    framework.register_agent(retrieval_agent)
    
    # Process in batches
    batch_size = 50
    total_chunks = 0
    
    for i in range(0, len(files), batch_size):
        batch = files[i:i+batch_size]
        print(f"  Processing batch {i//batch_size + 1}/{(len(files) + batch_size - 1)//batch_size}...", end="", flush=True)
        
        try:
            result = document_agent.process({"file_paths": [str(f) for f in batch]})
            chunks = result.get("chunks", [])
            if chunks:
                retrieval_agent.index_chunks(chunks)
                total_chunks += len(chunks)
            print(f" ✓ ({len(chunks)} chunks)")
        except Exception as e:
            print(f" ⚠️  Error: {e}")
    
    print()
    print(f"✓ Indexed {total_chunks:,} chunks from {len(files)} files")

if __name__ == "__main__":
    files = extract_all_databases()
    index_extracted_files(files)
