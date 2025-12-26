"""Compliance Tagging and Validation Tools"""

import json
import re
import os
from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime
import frontmatter


def tag_compliance_metadata(
    file_path: str,
    metadata: Dict[str, Any],
    schema_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Add compliance metadata tags to a markdown file
    
    Args:
        file_path: Path to markdown file
        metadata: Metadata dictionary to add
        schema_path: Path to compliance schema JSON (optional)
    
    Returns:
        Updated metadata dictionary
    """
    if schema_path is None:
        schema_path = "src/config/compliance_schema.json"
    
    # Load schema for validation
    schema = {}
    if os.path.exists(schema_path):
        with open(schema_path, 'r', encoding='utf-8') as f:
            schema_data = json.load(f)
            schema = schema_data.get('metadata_schema', {})
    
    # Validate and normalize metadata
    validated_metadata = _validate_metadata(metadata, schema)
    
    # Read existing file
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            post = frontmatter.load(f)
        
        # Merge metadata
        post.metadata.update(validated_metadata)
        
        # Write back
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(frontmatter.dumps(post))
    else:
        # Create new file with metadata
        post = frontmatter.Post("", **validated_metadata)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(frontmatter.dumps(post))
    
    return validated_metadata


def link_substance_to_regulation(
    substance_file: str,
    regulation_file: str,
    link_type: str = "regulated_by"
) -> Dict[str, Any]:
    """
    Create a link between a substance and a regulation
    
    Args:
        substance_file: Path to substance markdown file
        regulation_file: Path to regulation markdown file
        link_type: Type of link (e.g., "regulated_by", "restricted_in")
    
    Returns:
        Link metadata dictionary
    """
    link_metadata = {
        "link_type": link_type,
        "substance_file": substance_file,
        "regulation_file": regulation_file,
        "created_at": datetime.now().isoformat()
    }
    
    # Add link to substance file
    if os.path.exists(substance_file):
        with open(substance_file, 'r', encoding='utf-8') as f:
            post = frontmatter.load(f)
        
        if 'links' not in post.metadata:
            post.metadata['links'] = []
        
        post.metadata['links'].append({
            "type": link_type,
            "target": regulation_file,
            "created_at": link_metadata["created_at"]
        })
        
        with open(substance_file, 'w', encoding='utf-8') as f:
            f.write(frontmatter.dumps(post))
    
    # Add reverse link to regulation file
    if os.path.exists(regulation_file):
        with open(regulation_file, 'r', encoding='utf-8') as f:
            post = frontmatter.load(f)
        
        if 'linked_substances' not in post.metadata:
            post.metadata['linked_substances'] = []
        
        post.metadata['linked_substances'].append({
            "type": link_type,
            "target": substance_file,
            "created_at": link_metadata["created_at"]
        })
        
        with open(regulation_file, 'w', encoding='utf-8') as f:
            f.write(frontmatter.dumps(post))
    
    return link_metadata


def extract_hazard_classification(
    text: str,
    source: str = "REACH"
) -> List[str]:
    """
    Extract hazard classifications from text
    
    Args:
        text: Text to analyze
        source: Data source identifier
    
    Returns:
        List of hazard tags
    """
    hazard_keywords = {
        "carcinogenic": ["carcinogen", "cancer", "carcinogenic", "carcinogenicity"],
        "mutagenic": ["mutagen", "mutagenic", "mutagenicity", "genetic damage"],
        "reprotoxic": ["reprotoxic", "reproductive", "fertility", "developmental"],
        "persistent": ["persistent", "persistence", "degradation"],
        "bioaccumulative": ["bioaccumulative", "bioaccumulation", "bioaccumulate"],
        "toxic": ["toxic", "toxicity", "poisonous"],
        "endocrine_disruptor": ["endocrine", "hormone", "disruptor"],
        "respiratory_sensitizer": ["respiratory", "asthma", "breathing"],
        "skin_sensitizer": ["skin", "dermatitis", "allergen"],
        "flammable": ["flammable", "combustible", "ignition"],
        "explosive": ["explosive", "explosion", "detonation"],
        "oxidizing": ["oxidizing", "oxidizer", "oxidation"],
        "corrosive": ["corrosive", "corrosion", "acid", "base"],
        "environmental_hazard": ["environmental", "ecotoxic", "aquatic", "marine"]
    }
    
    text_lower = text.lower()
    found_hazards = []
    
    for hazard, keywords in hazard_keywords.items():
        if any(keyword in text_lower for keyword in keywords):
            found_hazards.append(hazard)
    
    return found_hazards


def normalize_chemical_identifier(
    identifier: str,
    identifier_type: str = "cas"
) -> Optional[str]:
    """
    Normalize chemical identifier (CAS or EC number)
    
    Args:
        identifier: Identifier to normalize
        identifier_type: Type of identifier ("cas" or "ec")
    
    Returns:
        Normalized identifier or None if invalid
    """
    if not identifier:
        return None
    
    # Remove whitespace and common separators
    normalized = re.sub(r'[\s\-]', '', identifier)
    
    if identifier_type.lower() == "cas":
        # CAS format: XXX-XX-X
        if len(normalized) >= 5:
            # Re-insert hyphens
            cas = f"{normalized[:-3]}-{normalized[-3:-1]}-{normalized[-1]}"
            # Validate
            from ..tools.reach_tools import validate_cas_number
            if validate_cas_number(cas):
                return cas
    elif identifier_type.lower() == "ec":
        # EC format: XXX-XXX-X
        if len(normalized) >= 7:
            ec = f"{normalized[:3]}-{normalized[3:6]}-{normalized[6]}"
            # Validate
            from ..tools.reach_tools import validate_ec_number
            if validate_ec_number(ec):
                return ec
    
    return None


def extract_compliance_tags_from_text(
    text: str
) -> Dict[str, Any]:
    """
    Extract compliance-related tags from text using pattern matching
    
    Args:
        text: Text to analyze
    
    Returns:
        Dictionary of extracted tags
    """
    tags = {
        "hazard_tags": extract_hazard_classification(text),
        "article_numbers": [],
        "cas_numbers": [],
        "ec_numbers": []
    }
    
    # Extract article numbers
    article_pattern = r'Article\s+(\d+)'
    articles = re.findall(article_pattern, text, re.IGNORECASE)
    tags["article_numbers"] = [f"Article {a}" for a in articles]
    
    # Extract CAS numbers
    cas_pattern = r'\b\d{2,7}-\d{2}-\d\b'
    cas_numbers = re.findall(cas_pattern, text)
    tags["cas_numbers"] = list(set(cas_numbers))  # Remove duplicates
    
    # Extract EC numbers
    ec_pattern = r'\b\d{3}-\d{3}-\d\b'
    ec_numbers = re.findall(ec_pattern, text)
    tags["ec_numbers"] = list(set(ec_numbers))  # Remove duplicates
    
    return tags


def validate_prop65_metadata(
    metadata: Dict[str, Any],
    schema_path: Optional[str] = None
) -> tuple[bool, List[str]]:
    """
    Validate Prop 65 specific metadata
    
    Args:
        metadata: Metadata dictionary to validate
        schema_path: Path to compliance schema JSON
    
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    
    # Check Prop 65 specific fields
    if metadata.get('source') == 'Prop65' or metadata.get('source') == 'OEHHA':
        # Check toxicity_type
        if 'toxicity_type' in metadata:
            if metadata['toxicity_type'] not in ['cancer', 'reproductive', 'both']:
                errors.append(f"Invalid toxicity_type: {metadata['toxicity_type']}")
        
        # Check date_listed format
        if 'date_listed' in metadata and metadata['date_listed']:
            try:
                datetime.strptime(metadata['date_listed'], '%Y-%m-%d')
            except:
                errors.append(f"Invalid date_listed format: {metadata['date_listed']}")
        
        # Validate NSRL/MADL if present
        if 'nsrl_value' in metadata and metadata['nsrl_value']:
            if not isinstance(metadata['nsrl_value'], (int, float)):
                errors.append("nsrl_value must be a number")
        
        if 'madl_value' in metadata and metadata['madl_value']:
            if not isinstance(metadata['madl_value'], (int, float)):
                errors.append("madl_value must be a number")
    
    return (len(errors) == 0, errors)


def validate_compliance_metadata(
    metadata: Dict[str, Any],
    schema_path: Optional[str] = None
) -> tuple[bool, List[str]]:
    """
    Validate compliance metadata against schema
    
    Args:
        metadata: Metadata dictionary to validate
        schema_path: Path to compliance schema JSON
    
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    if schema_path is None:
        schema_path = "src/config/compliance_schema.json"
    
    errors = []
    
    # Load schema
    if not os.path.exists(schema_path):
        return (False, [f"Schema file not found: {schema_path}"])
    
    with open(schema_path, 'r', encoding='utf-8') as f:
        schema_data = json.load(f)
    
    schema = schema_data.get('metadata_schema', {})
    tagging_rules = schema_data.get('tagging_rules', {})
    
    # Get document type
    doc_type = metadata.get('type')
    if not doc_type:
        errors.append("Missing required field: type")
        return (False, errors)
    
    # Check required fields for this type
    if doc_type in tagging_rules:
        required_fields = tagging_rules[doc_type].get('required_fields', [])
        for field in required_fields:
            if field not in metadata or not metadata[field]:
                errors.append(f"Missing required field for type '{doc_type}': {field}")
    
    # Validate CAS number format if present
    if 'cas_number' in metadata and metadata['cas_number']:
        from ..tools.reach_tools import validate_cas_number
        if not validate_cas_number(metadata['cas_number']):
            errors.append(f"Invalid CAS number format: {metadata['cas_number']}")
    
    # Validate EC number format if present
    if 'ec_number' in metadata and metadata['ec_number']:
        from ..tools.reach_tools import validate_ec_number
        if not validate_ec_number(metadata['ec_number']):
            errors.append(f"Invalid EC number format: {metadata['ec_number']}")
    
    # Validate article number format if present
    if 'article_number' in metadata and metadata['article_number']:
        article_pattern = r'^Article\s+\d+$'
        if not re.match(article_pattern, metadata['article_number'], re.IGNORECASE):
            errors.append(f"Invalid article number format: {metadata['article_number']}")
    
    # Also validate Prop 65 specific fields if present
    prop65_valid, prop65_errors = validate_prop65_metadata(metadata, schema_path)
    if not prop65_valid:
        errors.extend(prop65_errors)
    
    return (len(errors) == 0, errors)


def _validate_metadata(
    metadata: Dict[str, Any],
    schema: Dict[str, Any]
) -> Dict[str, Any]:
    """Internal function to validate and normalize metadata"""
    validated = {}
    
    # Copy and validate each field
    for key, value in metadata.items():
        if key in schema:
            field_schema = schema[key]
            
            # Type validation
            expected_type = field_schema.get('type')
            if expected_type == 'string' and not isinstance(value, str):
                value = str(value)
            elif expected_type == 'array' and not isinstance(value, list):
                value = [value] if value else []
            
            # Enum validation
            if 'enum' in field_schema:
                if value not in field_schema['enum']:
                    # Try to find close match
                    value_lower = str(value).lower()
                    for enum_val in field_schema['enum']:
                        if enum_val.lower() == value_lower:
                            value = enum_val
                            break
                    else:
                        # Use default if available
                        if 'default' in field_schema:
                            value = field_schema['default']
            
            validated[key] = value
        else:
            # Unknown field, include anyway
            validated[key] = value
    
    return validated

