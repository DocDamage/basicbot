"""Run REACH pipeline and index the generated markdown files"""

import sys
import os
import subprocess
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

print("=" * 70)
print("REACH DATA PIPELINE - EXTRACT AND INDEX")
print("=" * 70)
print()

# 1. Check if pipeline is extracted
pipeline_dir = Path("data/reach_pipeline")
if not pipeline_dir.exists():
    print("❌ REACH pipeline not found. Extracting ZIP file...")
    import zipfile
    zip_path = Path("reach_md_pipeline_per_substance_v1.zip")
    if zip_path.exists():
        with zipfile.ZipFile(zip_path, 'r') as z:
            z.extractall("data/reach_pipeline")
        print("✓ Extracted to data/reach_pipeline/")
    else:
        print(f"❌ ZIP file not found: {zip_path}")
        sys.exit(1)

print("1. CHECKING DEPENDENCIES")
print("-" * 70)

# Check if required packages are installed
required_packages = ['pandas', 'requests', 'beautifulsoup4', 'openpyxl']
missing = []

for pkg in required_packages:
    try:
        __import__(pkg.replace('-', '_'))
        print(f"  ✓ {pkg}")
    except ImportError:
        print(f"  ⚠️  {pkg} - MISSING")
        missing.append(pkg)

if missing:
    print(f"\n  Installing missing packages: {', '.join(missing)}")
    subprocess.run([sys.executable, "-m", "pip", "install"] + missing, check=False)
    print("  ✓ Dependencies installed")

print()

# 2. Run the REACH pipeline
print("2. RUNNING REACH PIPELINE")
print("-" * 70)
print("  This will scrape REACH data from ECHA websites...")
print("  (This may take several minutes)")
print()

pipeline_script = pipeline_dir / "run_all.py"
if pipeline_script.exists():
    try:
        # Change to pipeline directory and set PYTHONPATH
        original_dir = os.getcwd()
        original_path = os.environ.get("PYTHONPATH", "")
        
        try:
            os.chdir(pipeline_dir)
            os.environ["PYTHONPATH"] = str(pipeline_dir)
            
            print("  Running pipeline...")
            result = subprocess.run(
                [sys.executable, "run_all.py"],
                capture_output=True,
                text=True,
                timeout=600,  # 10 minute timeout
                cwd=str(pipeline_dir),
                env=dict(os.environ, PYTHONPATH=str(pipeline_dir))
            )
        finally:
            os.chdir(original_dir)
            if original_path:
                os.environ["PYTHONPATH"] = original_path
            elif "PYTHONPATH" in os.environ:
                del os.environ["PYTHONPATH"]
        
        if result.returncode == 0:
            print("  ✓ Pipeline completed successfully")
            if result.stdout:
                print("  Output:")
                for line in result.stdout.split('\n')[-10:]:  # Last 10 lines
                    if line.strip():
                        print(f"    {line}")
        else:
            print(f"  ⚠️  Pipeline exited with code {result.returncode}")
            if result.stderr:
                print("  Errors:")
                for line in result.stderr.split('\n')[-10:]:
                    if line.strip():
                        print(f"    {line}")
    except subprocess.TimeoutExpired:
        print("  ⚠️  Pipeline timed out (took longer than 10 minutes)")
        os.chdir(original_dir)
    except Exception as e:
        print(f"  ⚠️  Error running pipeline: {e}")
        os.chdir(original_dir)
else:
    print(f"  ❌ Pipeline script not found: {pipeline_script}")

print()

# 3. Check for generated markdown files
print("3. CHECKING GENERATED FILES")
print("-" * 70)

output_dir = pipeline_dir / "output" / "md"
markdown_files = []

if output_dir.exists():
    # Check for consolidated files
    consolidated_files = [
        "reach_svhc_candidate_list.md",
        "reach_annex_xiv_authorisation.md",
        "reach_annex_xvii_restrictions.md",
        "reach_cl_inventory.md"
    ]
    
    for filename in consolidated_files:
        filepath = output_dir / filename
        if filepath.exists():
            size = filepath.stat().st_size
            print(f"  ✓ {filename} ({size:,} bytes)")
            markdown_files.append(filepath)
        else:
            print(f"  ⚠️  {filename} - not generated")
    
    # Check for per-substance files
    per_substance_dir = output_dir / "per_substance"
    if per_substance_dir.exists():
        substance_files = list(per_substance_dir.rglob("*.md"))
        print(f"  ✓ Per-substance files: {len(substance_files)} files")
        markdown_files.extend(substance_files[:100])  # Limit for now
else:
    print("  ⚠️  Output directory not found")

print()

# 4. Copy files to extracted_docs and index
if markdown_files:
    print("4. INDEXING REACH DATA")
    print("-" * 70)
    
    # Copy to compliance directory
    compliance_dir = Path("data/extracted_docs/compliance/reach_substances")
    compliance_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"  Copying {len(markdown_files)} files to compliance directory...")
    copied_files = []
    
    for src_file in markdown_files:
        # Create relative path structure
        if "per_substance" in str(src_file):
            # Keep per-substance structure
            rel_path = src_file.relative_to(output_dir)
            dst_file = compliance_dir / rel_path
            dst_file.parent.mkdir(parents=True, exist_ok=True)
        else:
            # Copy consolidated files to root
            dst_file = compliance_dir / src_file.name
        
        try:
            import shutil
            shutil.copy2(src_file, dst_file)
            copied_files.append(dst_file)
        except Exception as e:
            print(f"    ⚠️  Error copying {src_file.name}: {e}")
    
    print(f"  ✓ Copied {len(copied_files)} files")
    print()
    
    # Index the files
    print("  Indexing REACH markdown files...")
    try:
        from src.bmad.framework import BMADFramework
        from src.agents import DocumentAgent, RetrievalAgent
        from dotenv import load_dotenv
        
        load_dotenv()
        
        memory_path = os.getenv("CHAT_HISTORY_DIR", "./data/chat_history")
        framework = BMADFramework(memory_storage_path=memory_path)
        
        document_agent = DocumentAgent(framework=framework)
        retrieval_agent = RetrievalAgent(framework=framework)
        framework.register_agent(document_agent)
        framework.register_agent(retrieval_agent)
        
        # Process files in batches
        batch_size = 50
        total_chunks = 0
        
        for i in range(0, len(copied_files), batch_size):
            batch = copied_files[i:i+batch_size]
            print(f"    Processing batch {i//batch_size + 1}/{(len(copied_files) + batch_size - 1)//batch_size}...", end="", flush=True)
            
            try:
                result = document_agent.process({"file_paths": [str(f) for f in batch]})
                chunks = result.get("chunks", [])
                if chunks:
                    retrieval_agent.index_chunks(chunks)
                    total_chunks += len(chunks)
                print(f" ✓ ({len(chunks)} chunks)")
            except Exception as e:
                print(f" ⚠️  Error: {e}")
        
        print(f"  ✓ REACH data indexed: {total_chunks:,} chunks")
        
    except Exception as e:
        print(f"  ⚠️  Error indexing: {e}")
        import traceback
        traceback.print_exc()
else:
    print("  ⚠️  No markdown files to index")

print()
print("=" * 70)
print("REACH PIPELINE COMPLETE")
print("=" * 70)
print()
print("REACH data is now queryable in your chatbot!")
print("You can ask questions like:")
print("  - 'What substances are on the SVHC candidate list?'")
print("  - 'Show me REACH Annex XIV authorization requirements'")
print("  - 'What are the REACH restrictions for phthalates?'")
print()

