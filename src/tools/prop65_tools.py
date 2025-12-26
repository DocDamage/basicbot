"""Prop 65 Data Extraction and Processing Tools"""

import re
import json
import os
import csv
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from datetime import datetime
import requests
from bs4 import BeautifulSoup


def download_oehha_data(
    url: str,
    output_path: Optional[str] = None,
    file_type: Optional[str] = None
) -> str:
    """
    Download data from OEHHA website
    
    Args:
        url: URL to download from
        output_path: Path to save downloaded file
        file_type: File type hint ('excel', 'pdf', 'html', 'csv')
    
    Returns:
        Path to downloaded file
    """
    if output_path is None:
        output_dir = os.getenv("EXTRACTED_DOCS_DIR", "./data/extracted_docs")
        prop65_dir = Path(output_dir) / "compliance" / "prop65" / "raw"
        prop65_dir.mkdir(parents=True, exist_ok=True)
        
        # Determine file extension from URL or file_type
        if file_type:
            ext = {
                'excel': '.xlsx',
                'pdf': '.pdf',
                'html': '.html',
                'csv': '.csv'
            }.get(file_type.lower(), '.html')
        else:
            ext = Path(url).suffix or '.html'
        
        timestamp = datetime.now().strftime("%Y%m%d")
        filename = f"oehha_data_{timestamp}{ext}"
        output_path = str(prop65_dir / filename)
    
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        with open(output_path, 'wb') as f:
            f.write(response.content)
        
        print(f"Downloaded OEHHA data to: {output_path}")
        return output_path
    except Exception as e:
        print(f"Error downloading from {url}: {e}")
        raise


def parse_oehha_excel(
    file_path: str,
    sheet_name: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Parse Excel file from OEHHA
    
    Args:
        file_path: Path to Excel file
        sheet_name: Specific sheet to parse (None for first sheet)
    
    Returns:
        List of dictionaries with parsed data
    """
    try:
        import openpyxl
        
        workbook = openpyxl.load_workbook(file_path, data_only=True)
        sheet = workbook[sheet_name] if sheet_name else workbook.active
        
        # Read header row
        headers = [cell.value for cell in sheet[1]]
        
        # Read data rows
        data = []
        for row in sheet.iter_rows(min_row=2, values_only=True):
            if any(cell for cell in row):  # Skip empty rows
                row_dict = dict(zip(headers, row))
                data.append(row_dict)
        
        return data
    except ImportError:
        print("openpyxl not installed. Install with: pip install openpyxl")
        return []
    except Exception as e:
        print(f"Error parsing Excel file {file_path}: {e}")
        return []


def parse_oehha_pdf(
    file_path: str
) -> List[Dict[str, Any]]:
    """
    Parse PDF file from OEHHA
    
    Args:
        file_path: Path to PDF file
    
    Returns:
        List of dictionaries with parsed data
    """
    try:
        import pdfplumber
        
        data = []
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                # Extract tables
                tables = page.extract_tables()
                for table in tables:
                    if table and len(table) > 1:
                        # First row as headers
                        headers = [str(cell).strip() if cell else "" for cell in table[0]]
                        # Data rows
                        for row in table[1:]:
                            if any(cell for cell in row):
                                row_dict = {
                                    headers[i]: str(cell).strip() if cell else ""
                                    for i, cell in enumerate(row)
                                    if i < len(headers)
                                }
                                data.append(row_dict)
        
        return data
    except ImportError:
        print("pdfplumber not installed. Install with: pip install pdfplumber")
        return []
    except Exception as e:
        print(f"Error parsing PDF file {file_path}: {e}")
        return []


def parse_oehha_html(
    file_path: str,
    table_selector: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Parse HTML file from OEHHA
    
    Args:
        file_path: Path to HTML file or URL
        table_selector: CSS selector for table (None for first table)
    
    Returns:
        List of dictionaries with parsed data
    """
    try:
        # If URL, download first
        if file_path.startswith('http'):
            file_path = download_oehha_data(file_path, file_type='html')
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        soup = BeautifulSoup(content, 'html.parser')
        
        # Find table
        if table_selector:
            table = soup.select_one(table_selector)
        else:
            table = soup.find('table')
        
        if not table:
            return []
        
        # Extract headers
        headers = []
        header_row = table.find('tr')
        if header_row:
            headers = [th.get_text(strip=True) for th in header_row.find_all(['th', 'td'])]
        
        # Extract data rows
        data = []
        for row in table.find_all('tr')[1:]:  # Skip header row
            cells = [td.get_text(strip=True) for td in row.find_all(['td', 'th'])]
            if cells and any(cells):
                row_dict = dict(zip(headers, cells))
                data.append(row_dict)
        
        return data
    except Exception as e:
        print(f"Error parsing HTML file {file_path}: {e}")
        return []


def extract_prop65_chemical_list(
    source_path: Optional[str] = None,
    source_url: Optional[str] = None,
    output_dir: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Extract Prop 65 chemical list from OEHHA source
    
    Args:
        source_path: Path to source file (Excel, PDF, HTML, CSV)
        source_url: URL to download from OEHHA
        output_dir: Directory to save extracted data
    
    Returns:
        List of chemical dictionaries
    """
    if output_dir is None:
        output_dir = os.getenv("EXTRACTED_DOCS_DIR", "./data/extracted_docs")
    
    chemicals_dir = Path(output_dir) / "compliance" / "prop65"
    chemicals_dir.mkdir(parents=True, exist_ok=True)
    
    chemicals = []
    file_path = source_path
    
    # Download if URL provided
    if source_url and not source_path:
        file_path = download_oehha_data(source_url, file_type='excel')
    
    if not file_path or not os.path.exists(file_path):
        print("Note: Prop 65 chemical list source file required")
        print("Download from: https://oehha.ca.gov/proposition-65/proposition-65-list")
        return []
    
    # Archive raw file
    raw_dir = chemicals_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d")
    archived_path = raw_dir / f"chemical_list_{timestamp}{Path(file_path).suffix}"
    if not archived_path.exists():
        import shutil
        shutil.copy2(file_path, archived_path)
    
    # Parse based on file extension
    file_ext = Path(file_path).suffix.lower()
    
    if file_ext == '.xlsx' or file_ext == '.xls':
        raw_data = parse_oehha_excel(file_path)
    elif file_ext == '.pdf':
        raw_data = parse_oehha_pdf(file_path)
    elif file_ext == '.html' or file_ext == '.htm':
        raw_data = parse_oehha_html(file_path)
    elif file_ext == '.csv':
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            raw_data = list(reader)
    else:
        print(f"Unsupported file format: {file_ext}")
        return []
    
    # Normalize chemical entries
    for entry in raw_data:
        normalized = normalize_prop65_entry(entry)
        if normalized:
            chemicals.append(normalized)
    
    # Save to markdown
    chemicals_md = _chemicals_to_markdown(chemicals)
    chemicals_file = chemicals_dir / "chemicals.md"
    with open(chemicals_file, 'w', encoding='utf-8') as f:
        f.write(chemicals_md)
    
    return chemicals


def extract_nsrl_madl_thresholds(
    source_path: Optional[str] = None,
    source_url: Optional[str] = None,
    output_dir: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Extract NSRL and MADL threshold values
    
    Args:
        source_path: Path to source file
        source_url: URL to download from OEHHA
        output_dir: Directory to save extracted data
    
    Returns:
        List of threshold dictionaries
    """
    if output_dir is None:
        output_dir = os.getenv("EXTRACTED_DOCS_DIR", "./data/extracted_docs")
    
    prop65_dir = Path(output_dir) / "compliance" / "prop65"
    prop65_dir.mkdir(parents=True, exist_ok=True)
    
    thresholds = []
    file_path = source_path
    
    # Download if URL provided
    if source_url and not source_path:
        file_path = download_oehha_data(source_url, file_type='pdf')
    
    if not file_path or not os.path.exists(file_path):
        print("Note: NSRL/MADL source file required")
        return []
    
    # Archive raw file
    raw_dir = prop65_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d")
    archived_path = raw_dir / f"nsrl_madl_{timestamp}{Path(file_path).suffix}"
    if not archived_path.exists():
        import shutil
        shutil.copy2(file_path, archived_path)
    
    # Parse based on file extension
    file_ext = Path(file_path).suffix.lower()
    
    if file_ext == '.xlsx' or file_ext == '.xls':
        raw_data = parse_oehha_excel(file_path)
    elif file_ext == '.pdf':
        raw_data = parse_oehha_pdf(file_path)
    elif file_ext == '.html' or file_ext == '.htm':
        raw_data = parse_oehha_html(file_path)
    elif file_ext == '.csv':
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            raw_data = list(reader)
    else:
        print(f"Unsupported file format: {file_ext}")
        return []
    
    # Normalize threshold entries
    for entry in raw_data:
        threshold = _normalize_threshold_entry(entry)
        if threshold:
            thresholds.append(threshold)
    
    # Save to markdown
    thresholds_md = _thresholds_to_markdown(thresholds)
    thresholds_file = prop65_dir / "thresholds.md"
    with open(thresholds_file, 'w', encoding='utf-8') as f:
        f.write(thresholds_md)
    
    return thresholds


def extract_warning_rules(
    source_path: Optional[str] = None,
    source_url: Optional[str] = None,
    output_dir: Optional[str] = None
) -> Dict[str, Any]:
    """
    Extract warning language requirements
    
    Args:
        source_path: Path to source file
        source_url: URL to download from OEHHA
        output_dir: Directory to save extracted data
    
    Returns:
        Dictionary with warning rules
    """
    if output_dir is None:
        output_dir = os.getenv("EXTRACTED_DOCS_DIR", "./data/extracted_docs")
    
    prop65_dir = Path(output_dir) / "compliance" / "prop65"
    prop65_dir.mkdir(parents=True, exist_ok=True)
    
    file_path = source_path
    
    # Download if URL provided
    if source_url and not source_path:
        file_path = download_oehha_data(source_url, file_type='html')
    
    if not file_path or not os.path.exists(file_path):
        print("Note: Warning rules source file required")
        return {}
    
    # Archive raw file
    raw_dir = prop65_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d")
    archived_path = raw_dir / f"warning_rules_{timestamp}{Path(file_path).suffix}"
    if not archived_path.exists():
        import shutil
        shutil.copy2(file_path, archived_path)
    
    # Parse HTML or text
    file_ext = Path(file_path).suffix.lower()
    
    if file_ext == '.html' or file_ext == '.htm':
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        soup = BeautifulSoup(content, 'html.parser')
        # Extract text content
        text_content = soup.get_text(separator='\n', strip=True)
    else:
        with open(file_path, 'r', encoding='utf-8') as f:
            text_content = f.read()
    
    # Save to markdown
    warning_rules_md = _warning_rules_to_markdown(text_content)
    warning_rules_file = prop65_dir / "warning_rules.md"
    with open(warning_rules_file, 'w', encoding='utf-8') as f:
        f.write(warning_rules_md)
    
    return {
        "content": text_content,
        "extracted_at": datetime.now().isoformat()
    }


def normalize_prop65_entry(entry: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Normalize Prop 65 chemical entry to standard format
    
    Args:
        entry: Raw entry dictionary
    
    Returns:
        Normalized entry or None if invalid
    """
    normalized = {}
    
    # Extract CAS number
    cas_number = None
    for key in ['CAS', 'CAS Number', 'CAS No', 'CASNumber', 'cas_number']:
        if key in entry and entry[key]:
            cas_number = str(entry[key]).strip()
            break
    
    # Extract substance name
    substance_name = None
    for key in ['Chemical', 'Substance', 'Name', 'Chemical Name', 'substance_name']:
        if key in entry and entry[key]:
            substance_name = str(entry[key]).strip()
            break
    
    if not substance_name:
        return None
    
    normalized['substance_name'] = substance_name
    if cas_number:
        # Validate and normalize CAS number
        from ..tools.reach_tools import validate_cas_number, normalize_chemical_name
        if validate_cas_number(cas_number):
            normalized['cas_number'] = cas_number
        else:
            # Try to extract CAS from text
            cas_match = re.search(r'\b\d{2,7}-\d{2}-\d\b', cas_number)
            if cas_match and validate_cas_number(cas_match.group()):
                normalized['cas_number'] = cas_match.group()
    
    # Extract toxicity type
    toxicity_type = None
    for key in ['Type', 'Toxicity', 'Toxicity Type', 'Listing Type', 'toxicity_type']:
        if key in entry and entry[key]:
            toxicity_val = str(entry[key]).strip().lower()
            if 'cancer' in toxicity_val and ('reproductive' in toxicity_val or 'developmental' in toxicity_val):
                toxicity_type = 'both'
            elif 'cancer' in toxicity_val:
                toxicity_type = 'cancer'
            elif 'reproductive' in toxicity_val or 'developmental' in toxicity_val:
                toxicity_type = 'reproductive'
            break
    
    if toxicity_type:
        normalized['toxicity_type'] = toxicity_type
    else:
        # Default to cancer if not specified
        normalized['toxicity_type'] = 'cancer'
    
    # Extract date listed
    date_listed = None
    for key in ['Date Listed', 'Listing Date', 'Date', 'date_listed']:
        if key in entry and entry[key]:
            date_val = str(entry[key]).strip()
            # Try to parse date
            try:
                # Common date formats
                for fmt in ['%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y', '%Y/%m/%d']:
                    try:
                        date_listed = datetime.strptime(date_val, fmt).strftime('%Y-%m-%d')
                        break
                    except:
                        continue
            except:
                pass
            break
    
    if date_listed:
        normalized['date_listed'] = date_listed
    
    # Extract NSRL if present
    nsrl = None
    for key in ['NSRL', 'No Significant Risk Level', 'nsrl']:
        if key in entry and entry[key]:
            nsrl_val = str(entry[key]).strip()
            # Extract number and unit
            nsrl_match = re.search(r'([\d.]+)\s*([µµ]?g/day|mg/day|g/day)', nsrl_val, re.IGNORECASE)
            if nsrl_match:
                nsrl = {
                    'value': float(nsrl_match.group(1)),
                    'unit': nsrl_match.group(2).lower()
                }
            break
    
    if nsrl:
        normalized['nsrl'] = nsrl
    
    # Extract MADL if present
    madl = None
    for key in ['MADL', 'Maximum Allowable Dose Level', 'madl']:
        if key in entry and entry[key]:
            madl_val = str(entry[key]).strip()
            madl_match = re.search(r'([\d.]+)\s*([µµ]?g/day|mg/day|g/day)', madl_val, re.IGNORECASE)
            if madl_match:
                madl = {
                    'value': float(madl_match.group(1)),
                    'unit': madl_match.group(2).lower()
                }
            break
    
    if madl:
        normalized['madl'] = madl
    
    normalized['date_updated'] = datetime.now().isoformat()
    
    return normalized


def validate_prop65_listing(
    entry: Dict[str, Any]
) -> Tuple[bool, List[str]]:
    """
    Validate Prop 65 listing entry
    
    Args:
        entry: Entry dictionary to validate
    
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    
    # Check required fields
    if 'substance_name' not in entry or not entry['substance_name']:
        errors.append("Missing required field: substance_name")
    
    if 'toxicity_type' not in entry:
        errors.append("Missing required field: toxicity_type")
    elif entry['toxicity_type'] not in ['cancer', 'reproductive', 'both']:
        errors.append(f"Invalid toxicity_type: {entry['toxicity_type']}")
    
    if 'date_listed' not in entry or not entry['date_listed']:
        errors.append("Missing required field: date_listed")
    
    # Validate CAS number if present
    if 'cas_number' in entry and entry['cas_number']:
        from ..tools.reach_tools import validate_cas_number
        if not validate_cas_number(entry['cas_number']):
            errors.append(f"Invalid CAS number format: {entry['cas_number']}")
    
    # Validate date format
    if 'date_listed' in entry and entry['date_listed']:
        try:
            datetime.strptime(entry['date_listed'], '%Y-%m-%d')
        except:
            errors.append(f"Invalid date format: {entry['date_listed']}")
    
    return (len(errors) == 0, errors)


def calculate_exposure_compliance(
    cas_number: str,
    exposure_value: float,
    exposure_unit: str,
    threshold_type: str = "nsrl"
) -> Dict[str, Any]:
    """
    Check if exposure exceeds NSRL/MADL threshold
    
    Args:
        cas_number: CAS number of chemical
        exposure_value: Exposure value
        exposure_unit: Unit of exposure (must match threshold unit)
        threshold_type: "nsrl" or "madl"
    
    Returns:
        Dictionary with compliance status
    """
    # This would typically query the stored thresholds
    # For now, return structure
    return {
        "cas_number": cas_number,
        "exposure_value": exposure_value,
        "exposure_unit": exposure_unit,
        "threshold_type": threshold_type,
        "exceeds_threshold": None,  # Would be calculated from actual threshold
        "compliance_status": "unknown"
    }


def generate_warning_text(
    cas_number: Optional[str] = None,
    substance_name: Optional[str] = None,
    warning_type: str = "consumer_product"
) -> str:
    """
    Generate required Prop 65 warning text
    
    Args:
        cas_number: CAS number (optional)
        substance_name: Substance name (optional)
        warning_type: Type of warning (consumer_product, occupational, environmental)
    
    Returns:
        Warning text
    """
    base_warning = "WARNING: This product contains chemicals known to the State of California to cause cancer and/or birth defects or other reproductive harm."
    
    if warning_type == "consumer_product":
        return base_warning
    elif warning_type == "occupational":
        return f"WARNING: This workplace contains chemicals known to the State of California to cause cancer and/or birth defects or other reproductive harm."
    elif warning_type == "environmental":
        return f"WARNING: This area contains chemicals known to the State of California to cause cancer and/or birth defects or other reproductive harm."
    
    return base_warning


# Helper functions for markdown conversion

def _chemicals_to_markdown(chemicals: List[Dict[str, Any]]) -> str:
    """Convert chemicals list to markdown format"""
    lines = []
    lines.append("# Prop 65 Chemical List")
    lines.append("")
    lines.append(f"*Last updated: {datetime.now().strftime('%Y-%m-%d')}*")
    lines.append("")
    lines.append("## Chemicals")
    lines.append("")
    
    for chem in chemicals:
        lines.append("---")
        lines.append(f"source: Prop65")
        lines.append(f"type: chemical")
        lines.append(f"jurisdiction: US-CA")
        lines.append(f"domain: chemical_regulation")
        
        if chem.get('cas_number'):
            lines.append(f"cas_number: {chem['cas_number']}")
        if chem.get('substance_name'):
            lines.append(f"substance_name: {chem['substance_name']}")
        if chem.get('toxicity_type'):
            lines.append(f"toxicity_type: {chem['toxicity_type']}")
        if chem.get('date_listed'):
            lines.append(f"date_listed: {chem['date_listed']}")
        if chem.get('nsrl'):
            nsrl = chem['nsrl']
            lines.append(f"nsrl_value: {nsrl.get('value', '')}")
            lines.append(f"nsrl_unit: {nsrl.get('unit', '')}")
        if chem.get('madl'):
            madl = chem['madl']
            lines.append(f"madl_value: {madl.get('value', '')}")
            lines.append(f"madl_unit: {madl.get('unit', '')}")
        
        lines.append("---")
        lines.append("")
        lines.append(f"## {chem.get('substance_name', 'Unknown')}")
        lines.append("")
        
        if chem.get('cas_number'):
            lines.append(f"**CAS Number:** {chem['cas_number']}")
            lines.append("")
        if chem.get('toxicity_type'):
            lines.append(f"**Toxicity Type:** {chem['toxicity_type'].title()}")
            lines.append("")
        if chem.get('date_listed'):
            lines.append(f"**Date Listed:** {chem['date_listed']}")
            lines.append("")
        if chem.get('nsrl'):
            nsrl = chem['nsrl']
            lines.append(f"**NSRL:** {nsrl.get('value', '')} {nsrl.get('unit', '')}")
            lines.append("")
        if chem.get('madl'):
            madl = chem['madl']
            lines.append(f"**MADL:** {madl.get('value', '')} {madl.get('unit', '')}")
            lines.append("")
        
        lines.append("")
    
    return "\n".join(lines)


def _thresholds_to_markdown(thresholds: List[Dict[str, Any]]) -> str:
    """Convert thresholds list to markdown format"""
    lines = []
    lines.append("# Prop 65 NSRL and MADL Thresholds")
    lines.append("")
    lines.append(f"*Last updated: {datetime.now().strftime('%Y-%m-%d')}*")
    lines.append("")
    lines.append("## Thresholds")
    lines.append("")
    
    for threshold in thresholds:
        lines.append("---")
        lines.append(f"source: Prop65")
        lines.append(f"type: threshold")
        lines.append(f"jurisdiction: US-CA")
        lines.append(f"domain: chemical_regulation")
        
        if threshold.get('cas_number'):
            lines.append(f"cas_number: {threshold['cas_number']}")
        if threshold.get('substance_name'):
            lines.append(f"substance_name: {threshold['substance_name']}")
        if threshold.get('nsrl'):
            nsrl = threshold['nsrl']
            lines.append(f"nsrl_value: {nsrl.get('value', '')}")
            lines.append(f"nsrl_unit: {nsrl.get('unit', '')}")
        if threshold.get('madl'):
            madl = threshold['madl']
            lines.append(f"madl_value: {madl.get('value', '')}")
            lines.append(f"madl_unit: {madl.get('unit', '')}")
        
        lines.append("---")
        lines.append("")
        lines.append(f"## {threshold.get('substance_name', 'Unknown')}")
        lines.append("")
        
        if threshold.get('nsrl'):
            nsrl = threshold['nsrl']
            lines.append(f"**NSRL:** {nsrl.get('value', '')} {nsrl.get('unit', '')}")
            lines.append("")
        if threshold.get('madl'):
            madl = threshold['madl']
            lines.append(f"**MADL:** {madl.get('value', '')} {madl.get('unit', '')}")
            lines.append("")
        
        lines.append("")
    
    return "\n".join(lines)


def _normalize_threshold_entry(entry: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Normalize threshold entry"""
    normalized = {}
    
    # Extract CAS and substance name (similar to normalize_prop65_entry)
    cas_number = None
    for key in ['CAS', 'CAS Number', 'CAS No', 'cas_number']:
        if key in entry and entry[key]:
            cas_number = str(entry[key]).strip()
            break
    
    substance_name = None
    for key in ['Chemical', 'Substance', 'Name', 'substance_name']:
        if key in entry and entry[key]:
            substance_name = str(entry[key]).strip()
            break
    
    if not substance_name:
        return None
    
    normalized['substance_name'] = substance_name
    if cas_number:
        from ..tools.reach_tools import validate_cas_number
        if validate_cas_number(cas_number):
            normalized['cas_number'] = cas_number
    
    # Extract NSRL
    for key in ['NSRL', 'No Significant Risk Level', 'nsrl']:
        if key in entry and entry[key]:
            nsrl_val = str(entry[key]).strip()
            nsrl_match = re.search(r'([\d.]+)\s*([µµ]?g/day|mg/day|g/day)', nsrl_val, re.IGNORECASE)
            if nsrl_match:
                normalized['nsrl'] = {
                    'value': float(nsrl_match.group(1)),
                    'unit': nsrl_match.group(2).lower()
                }
            break
    
    # Extract MADL
    for key in ['MADL', 'Maximum Allowable Dose Level', 'madl']:
        if key in entry and entry[key]:
            madl_val = str(entry[key]).strip()
            madl_match = re.search(r'([\d.]+)\s*([µµ]?g/day|mg/day|g/day)', madl_val, re.IGNORECASE)
            if madl_match:
                normalized['madl'] = {
                    'value': float(madl_match.group(1)),
                    'unit': madl_match.group(2).lower()
                }
            break
    
    return normalized if (normalized.get('nsrl') or normalized.get('madl')) else None


def _warning_rules_to_markdown(content: str) -> str:
    """Convert warning rules to markdown format"""
    lines = []
    lines.append("# Prop 65 Warning Requirements")
    lines.append("")
    lines.append(f"*Last updated: {datetime.now().strftime('%Y-%m-%d')}*")
    lines.append("")
    lines.append("## Warning Rules")
    lines.append("")
    lines.append(content)
    lines.append("")
    lines.append("## Source Attribution")
    lines.append("")
    lines.append("Data sourced from California Office of Environmental Health Hazard Assessment (OEHHA)")
    lines.append("")
    lines.append("Official website: https://oehha.ca.gov/proposition-65")
    
    return "\n".join(lines)

