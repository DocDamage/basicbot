"""Script to organize files into proper folders"""

import os
import shutil
from pathlib import Path

# Get project root
project_root = Path(__file__).parent

# Create directories
directories = {
    'docs': project_root / 'docs',
    'scripts': project_root / 'scripts',
    'data_archives': project_root / 'data' / 'archives',
    'data_plans': project_root / 'data' / 'plans'
}

for dir_path in directories.values():
    # Remove if it's a file
    if dir_path.exists() and dir_path.is_file():
        dir_path.unlink()
    # Create directory
    try:
        dir_path.mkdir(parents=True, exist_ok=True)
    except FileExistsError:
        # Directory already exists, that's fine
        pass

# Files to move
files_to_move = {
    # Documentation files
    'docs': [
        '*.md',
        '*.json'
    ],
    # Scripts
    'scripts': [
        '*.py',
        '*.bat'
    ],
    # Archives
    'data_archives': [
        '*.zip',
        '*.pdf'
    ]
}

# Keep these files in root
keep_in_root = {
    'README.md',
    'requirements.txt',
    'process_books.py',  # Main entry point
    'src',
    'data',
    'books',
    'organize_files.py'
}

# Move markdown files (except README.md)
print("Moving documentation files...")
for md_file in project_root.glob('*.md'):
    if md_file.name not in keep_in_root:
        try:
            shutil.move(str(md_file), str(directories['docs'] / md_file.name))
            print(f"  Moved: {md_file.name} -> docs/")
        except Exception as e:
            print(f"  Error moving {md_file.name}: {e}")

# Move JSON files
print("\nMoving JSON files...")
for json_file in project_root.glob('*.json'):
    if json_file.name not in keep_in_root:
        try:
            shutil.move(str(json_file), str(directories['docs'] / json_file.name))
            print(f"  Moved: {json_file.name} -> docs/")
        except Exception as e:
            print(f"  Error moving {json_file.name}: {e}")

# Move Python scripts (except main entry points)
print("\nMoving Python scripts...")
main_scripts = {'process_books.py', 'organize_files.py', '__init__.py'}
for py_file in project_root.glob('*.py'):
    if py_file.name not in main_scripts and py_file.name not in keep_in_root:
        try:
            shutil.move(str(py_file), str(directories['scripts'] / py_file.name))
            print(f"  Moved: {py_file.name} -> scripts/")
        except Exception as e:
            print(f"  Error moving {py_file.name}: {e}")

# Move batch files
print("\nMoving batch files...")
for bat_file in project_root.glob('*.bat'):
    try:
        shutil.move(str(bat_file), str(directories['scripts'] / bat_file.name))
        print(f"  Moved: {bat_file.name} -> scripts/")
    except Exception as e:
        print(f"  Error moving {bat_file.name}: {e}")

# Move ZIP files
print("\nMoving ZIP files...")
for zip_file in project_root.glob('*.zip'):
    try:
        shutil.move(str(zip_file), str(directories['data_archives'] / zip_file.name))
        print(f"  Moved: {zip_file.name} -> data/archives/")
    except Exception as e:
        print(f"  Error moving {zip_file.name}: {e}")

# Move PDF files (except those in books folder)
print("\nMoving PDF files...")
for pdf_file in project_root.glob('*.pdf'):
    if 'books' not in str(pdf_file):
        try:
            shutil.move(str(pdf_file), str(directories['data_archives'] / pdf_file.name))
            print(f"  Moved: {pdf_file.name} -> data/archives/")
        except Exception as e:
            print(f"  Error moving {pdf_file.name}: {e}")

# Move plan files to data/plans
print("\nOrganizing plan files...")
plan_files = list(directories['docs'].glob('*PLAN*.md')) + list(directories['docs'].glob('*PLAN*.json'))
for plan_file in plan_files:
    try:
        shutil.move(str(plan_file), str(directories['data_plans'] / plan_file.name))
        print(f"  Moved: {plan_file.name} -> data/plans/")
    except Exception as e:
        print(f"  Error moving {plan_file.name}: {e}")

print("\n✓ File organization complete!")
print(f"\nDirectory structure:")
print(f"  docs/ - Documentation files")
print(f"  scripts/ - Utility scripts")
print(f"  data/archives/ - ZIP and PDF archives")
print(f"  data/plans/ - Integration plans")

