"""REACH Data Extraction Tools"""

import re
import json
import os
from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime
import requests
from bs4 import BeautifulSoup


def extract_echa_substances(
    output_dir: Optional[str] = None,
    limit: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Extract substance data from ECHA database
    
    Args:
        output_dir: Directory to save extracted data
        limit: Maximum number of substances to extract (None for all)
    
    Returns:
        List of substance dictionaries
    """
    if output_dir is None:
        output_dir = os.getenv("EXTRACTED_DOCS_DIR", "./data/extracted_docs")
    
    substances_dir = Path(output_dir) / "reach_substances" / "registered_substances"
    substances_dir.mkdir(parents=True, exist_ok=True)
    
    substances = []
    
    # ECHA API endpoint (example - may need to be updated)
    # Note: ECHA API integration requires API keys and proper endpoints
    # This is a template implementation that can be extended with actual API calls
    echa_api_base = "https://echa.europa.eu/api"
    
    try:
        # Example: Fetch SVHC list (candidate list)
        # In production, you would implement proper API calls here
        print("Note: ECHA API integration requires API keys and proper endpoints")
        print("This is a template implementation for REACH data extraction")
        
        # Template structure for substance data (extend with actual API response parsing)
        # Real implementation would parse actual ECHA responses
        sample_substance = {
            "substance_name": "Example Substance",
            "cas_number": None,
            "ec_number": None,
            "reach_status": "registered",
            "hazard_tags": [],
            "date_updated": datetime.now().isoformat()
        }
        
        # Save to markdown file
        md_content = _substance_to_markdown(sample_substance)
        filename = f"substance_{sample_substance.get('cas_number', 'unknown')}.md"
        filepath = substances_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(md_content)
        
        substances.append(sample_substance)
        
    except Exception as e:
        print(f"Error extracting ECHA substances: {e}")
    
    return substances


def extract_reach_regulation(
    output_dir: Optional[str] = None,
    articles: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """
    Extract REACH Regulation text from EUR-Lex or other sources
    
    Args:
        output_dir: Directory to save extracted articles
        articles: List of article numbers to extract (None for all)
    
    Returns:
        List of article dictionaries
    """
    if output_dir is None:
        output_dir = os.getenv("EXTRACTED_DOCS_DIR", "./data/extracted_docs")
    
    articles_dir = Path(output_dir) / "reach_regulation" / "articles"
    articles_dir.mkdir(parents=True, exist_ok=True)
    
    extracted_articles = []
    
    # EUR-Lex API or web scraping
    # Note: This is a placeholder implementation
    # Real implementation would parse EUR-Lex documents
    
    try:
        # Example article structure
        # In production, you would fetch actual regulation text
        print("Note: EUR-Lex integration requires proper document parsing")
        print("This is a template implementation for REACH regulation extraction")
        
        # Template article structure (extend with actual regulation parsing)
        sample_article = {
            "article_number": "Article 33",
            "title": "Duty to communicate information on substances in articles",
            "content": "Any supplier of an article containing a substance meeting the criteria...",
            "jurisdiction": "EU",
            "date_updated": datetime.now().isoformat()
        }
        
        # Save to markdown
        md_content = _article_to_markdown(sample_article)
        filename = f"article_{sample_article['article_number'].replace(' ', '_').lower()}.md"
        filepath = articles_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(md_content)
        
        extracted_articles.append(sample_article)
        
    except Exception as e:
        print(f"Error extracting REACH regulation: {e}")
    
    return extracted_articles


def extract_plastchem_data(
    output_dir: Optional[str] = None,
    source_path: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Extract data from PlastChem database
    
    Args:
        output_dir: Directory to save extracted data
        source_path: Path to PlastChem database file (CSV, JSON, etc.)
    
    Returns:
        List of chemical dictionaries
    """
    if output_dir is None:
        output_dir = os.getenv("EXTRACTED_DOCS_DIR", "./data/extracted_docs")
    
    plastchem_dir = Path(output_dir) / "plastchem" / "hazardous_chemicals"
    plastchem_dir.mkdir(parents=True, exist_ok=True)
    
    chemicals = []
    
    try:
        # If source_path provided, read from file
        if source_path and os.path.exists(source_path):
            # Parse CSV, JSON, or other format
            if source_path.endswith('.json'):
                with open(source_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    chemicals = data if isinstance(data, list) else [data]
            elif source_path.endswith('.csv'):
                import csv
                with open(source_path, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    chemicals = list(reader)
        else:
            print("Note: PlastChem data extraction requires source file")
            print("This is a template implementation")
        
        # Save each chemical to markdown
        for chemical in chemicals:
            md_content = _chemical_to_markdown(chemical)
            cas = chemical.get('cas_number', 'unknown')
            filename = f"plastchem_{cas}.md"
            filepath = plastchem_dir / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(md_content)
        
    except Exception as e:
        print(f"Error extracting PlastChem data: {e}")
    
    return chemicals


def normalize_chemical_name(name: str) -> str:
    """
    Normalize chemical name (remove extra spaces, standardize format)
    
    Args:
        name: Chemical name to normalize
    
    Returns:
        Normalized chemical name
    """
    if not name:
        return ""
    
    # Remove extra whitespace
    normalized = re.sub(r'\s+', ' ', name.strip())
    
    # Standardize common prefixes/suffixes
    normalized = re.sub(r'\s*\([^)]*\)\s*', '', normalized)  # Remove parenthetical notes
    
    return normalized


def validate_cas_number(cas_number: str) -> bool:
    """
    Validate CAS registry number format
    
    Args:
        cas_number: CAS number to validate (format: XXX-XX-X)
    
    Returns:
        True if valid format
    """
    if not cas_number:
        return False
    
    # CAS number pattern: 2-7 digits, hyphen, 2 digits, hyphen, 1 digit
    pattern = r'^\d{2,7}-\d{2}-\d$'
    
    if not re.match(pattern, cas_number):
        return False
    
    # Validate checksum (last digit)
    parts = cas_number.split('-')
    digits = parts[0] + parts[1]
    check_digit = int(parts[2])
    
    # Calculate checksum
    total = sum(int(d) * (len(digits) - i) for i, d in enumerate(digits))
    calculated_check = total % 10
    
    return calculated_check == check_digit


def validate_ec_number(ec_number: str) -> bool:
    """
    Validate EC number format
    
    Args:
        ec_number: EC number to validate (format: XXX-XXX-X)
    
    Returns:
        True if valid format
    """
    if not ec_number:
        return False
    
    # EC number pattern: 3 digits, hyphen, 3 digits, hyphen, 1 digit
    pattern = r'^\d{3}-\d{3}-\d$'
    
    return bool(re.match(pattern, ec_number))


def extract_article_number(text: str) -> Optional[str]:
    """
    Extract REACH article number from text
    
    Args:
        text: Text containing article reference
    
    Returns:
        Article number (e.g., "Article 33") or None
    """
    pattern = r'Article\s+(\d+)'
    match = re.search(pattern, text, re.IGNORECASE)
    
    if match:
        return f"Article {match.group(1)}"
    
    return None


# Helper functions for markdown conversion

def _substance_to_markdown(substance: Dict[str, Any]) -> str:
    """Convert substance dict to markdown format"""
    lines = []
    lines.append("---")
    lines.append(f"source: REACH")
    lines.append(f"type: substance")
    lines.append(f"jurisdiction: EU")
    lines.append(f"domain: chemical_regulation")
    
    if substance.get('cas_number'):
        lines.append(f"cas_number: {substance['cas_number']}")
    if substance.get('ec_number'):
        lines.append(f"ec_number: {substance['ec_number']}")
    if substance.get('substance_name'):
        lines.append(f"substance_name: {substance['substance_name']}")
    if substance.get('reach_status'):
        lines.append(f"reach_status: {substance['reach_status']}")
    if substance.get('hazard_tags'):
        lines.append(f"hazard_tags: {json.dumps(substance['hazard_tags'])}")
    if substance.get('chemical_class'):
        lines.append(f"chemical_class: {substance['chemical_class']}")
    if substance.get('date_updated'):
        lines.append(f"date_updated: {substance['date_updated']}")
    
    lines.append("---")
    lines.append("")
    lines.append(f"# {substance.get('substance_name', 'Unknown Substance')}")
    lines.append("")
    
    if substance.get('cas_number'):
        lines.append(f"**CAS Number:** {substance['cas_number']}")
        lines.append("")
    if substance.get('ec_number'):
        lines.append(f"**EC Number:** {substance['ec_number']}")
        lines.append("")
    if substance.get('reach_status'):
        lines.append(f"**REACH Status:** {substance['reach_status']}")
        lines.append("")
    if substance.get('hazard_tags'):
        lines.append(f"**Hazard Classifications:** {', '.join(substance['hazard_tags'])}")
        lines.append("")
    
    return "\n".join(lines)


def _article_to_markdown(article: Dict[str, Any]) -> str:
    """Convert article dict to markdown format"""
    lines = []
    lines.append("---")
    lines.append(f"source: REACH")
    lines.append(f"type: article")
    lines.append(f"jurisdiction: EU")
    lines.append(f"domain: chemical_regulation")
    lines.append(f"article_number: {article.get('article_number', '')}")
    
    if article.get('date_updated'):
        lines.append(f"date_updated: {article['date_updated']}")
    
    lines.append("---")
    lines.append("")
    lines.append(f"# {article.get('article_number', 'Article')}: {article.get('title', '')}")
    lines.append("")
    lines.append(article.get('content', ''))
    
    return "\n".join(lines)


def _chemical_to_markdown(chemical: Dict[str, Any]) -> str:
    """Convert chemical dict to markdown format"""
    lines = []
    lines.append("---")
    lines.append(f"source: PlastChem")
    lines.append(f"type: substance")
    lines.append(f"jurisdiction: EU")
    lines.append(f"domain: hazard_data")
    
    if chemical.get('cas_number'):
        lines.append(f"cas_number: {chemical['cas_number']}")
    if chemical.get('substance_name'):
        lines.append(f"substance_name: {chemical['substance_name']}")
    if chemical.get('hazard_tags'):
        if isinstance(chemical['hazard_tags'], list):
            lines.append(f"hazard_tags: {json.dumps(chemical['hazard_tags'])}")
        else:
            lines.append(f"hazard_tags: {chemical['hazard_tags']}")
    
    lines.append("---")
    lines.append("")
    lines.append(f"# {chemical.get('substance_name', 'Unknown Chemical')}")
    lines.append("")
    
    # Add all fields from chemical dict
    for key, value in chemical.items():
        if key not in ['substance_name', 'cas_number'] and value:
            lines.append(f"**{key.replace('_', ' ').title()}:** {value}")
            lines.append("")
    
    return "\n".join(lines)

