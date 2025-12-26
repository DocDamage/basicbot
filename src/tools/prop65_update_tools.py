"""Prop 65 Update Management and Version Tracking Tools"""

import json
import os
from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime
import difflib


def check_prop65_updates(
    current_version_dir: Optional[str] = None,
    oehha_url: Optional[str] = None
) -> Dict[str, Any]:
    """
    Check for new Prop 65 updates from OEHHA
    
    Args:
        current_version_dir: Directory with current version
        oehha_url: URL to check for updates
    
    Returns:
        Dictionary with update status
    """
    if current_version_dir is None:
        output_dir = os.getenv("EXTRACTED_DOCS_DIR", "./data/extracted_docs")
        current_version_dir = str(Path(output_dir) / "compliance" / "prop65")
    
    # Get latest version date
    versions_dir = Path(current_version_dir) / "versions"
    latest_version = _get_latest_version(versions_dir)
    
    # In a real implementation, this would:
    # 1. Check OEHHA website for publication dates
    # 2. Compare with latest_version
    # 3. Return update status
    
    return {
        "has_updates": False,
        "latest_version": latest_version,
        "checked_at": datetime.now().isoformat(),
        "update_available": False
    }


def compare_prop65_versions(
    version1_dir: str,
    version2_dir: str
) -> Dict[str, Any]:
    """
    Compare two Prop 65 versions and identify changes
    
    Args:
        version1_dir: Path to first version directory
        version2_dir: Path to second version directory
    
    Returns:
        Dictionary with comparison results
    """
    changes = {
        "added": [],
        "removed": [],
        "modified": [],
        "threshold_changes": []
    }
    
    v1_path = Path(version1_dir)
    v2_path = Path(version2_dir)
    
    # Compare chemicals.md files
    v1_chemicals_file = v1_path / "chemicals.md"
    v2_chemicals_file = v2_path / "chemicals.md"
    
    if v1_chemicals_file.exists() and v2_chemicals_file.exists():
        v1_chemicals = _parse_chemicals_file(v1_chemicals_file)
        v2_chemicals = _parse_chemicals_file(v2_chemicals_file)
        
        v1_cas = {c.get('cas_number'): c for c in v1_chemicals if c.get('cas_number')}
        v2_cas = {c.get('cas_number'): c for c in v2_chemicals if c.get('cas_number')}
        
        # Find added chemicals
        added_cas = set(v2_cas.keys()) - set(v1_cas.keys())
        changes["added"] = [v2_cas[cas] for cas in added_cas]
        
        # Find removed chemicals
        removed_cas = set(v1_cas.keys()) - set(v2_cas.keys())
        changes["removed"] = [v1_cas[cas] for cas in removed_cas]
        
        # Find modified chemicals
        common_cas = set(v1_cas.keys()) & set(v2_cas.keys())
        for cas in common_cas:
            v1_chem = v1_cas[cas]
            v2_chem = v2_cas[cas]
            if v1_chem != v2_chem:
                changes["modified"].append({
                    "cas_number": cas,
                    "old": v1_chem,
                    "new": v2_chem
                })
    
    # Compare thresholds.md files
    v1_thresholds_file = v1_path / "thresholds.md"
    v2_thresholds_file = v2_path / "thresholds.md"
    
    if v1_thresholds_file.exists() and v2_thresholds_file.exists():
        v1_thresholds = _parse_thresholds_file(v1_thresholds_file)
        v2_thresholds = _parse_thresholds_file(v2_thresholds_file)
        
        v1_thresh_dict = {t.get('cas_number'): t for t in v1_thresholds if t.get('cas_number')}
        v2_thresh_dict = {t.get('cas_number'): t for t in v2_thresholds if t.get('cas_number')}
        
        # Find threshold changes
        common_cas = set(v1_thresh_dict.keys()) & set(v2_thresh_dict.keys())
        for cas in common_cas:
            v1_thresh = v1_thresh_dict[cas]
            v2_thresh = v2_thresh_dict[cas]
            
            if v1_thresh.get('nsrl') != v2_thresh.get('nsrl') or \
               v1_thresh.get('madl') != v2_thresh.get('madl'):
                changes["threshold_changes"].append({
                    "cas_number": cas,
                    "old": v1_thresh,
                    "new": v2_thresh
                })
    
    return changes


def create_prop65_changelog(
    changes: Dict[str, Any],
    output_dir: Optional[str] = None
) -> str:
    """
    Generate changelog entry from version comparison
    
    Args:
        changes: Changes dictionary from compare_prop65_versions
        output_dir: Directory to save changelog
    
    Returns:
        Path to changelog file
    """
    if output_dir is None:
        output_dir = os.getenv("EXTRACTED_DOCS_DIR", "./data/extracted_docs")
    
    prop65_dir = Path(output_dir) / "compliance" / "prop65"
    prop65_dir.mkdir(parents=True, exist_ok=True)
    
    changelog_file = prop65_dir / "changelog.md"
    
    # Read existing changelog
    existing_content = ""
    if changelog_file.exists():
        with open(changelog_file, 'r', encoding='utf-8') as f:
            existing_content = f.read()
    
    # Create new entry
    timestamp = datetime.now().strftime("%Y-%m-%d")
    entry_lines = []
    entry_lines.append(f"## Update {timestamp}")
    entry_lines.append("")
    
    if changes.get("added"):
        entry_lines.append(f"### Added Chemicals ({len(changes['added'])})")
        entry_lines.append("")
        for chem in changes["added"]:
            cas = chem.get('cas_number', 'N/A')
            name = chem.get('substance_name', 'Unknown')
            entry_lines.append(f"- {name} (CAS: {cas})")
        entry_lines.append("")
    
    if changes.get("removed"):
        entry_lines.append(f"### Removed Chemicals ({len(changes['removed'])})")
        entry_lines.append("")
        for chem in changes["removed"]:
            cas = chem.get('cas_number', 'N/A')
            name = chem.get('substance_name', 'Unknown')
            entry_lines.append(f"- {name} (CAS: {cas})")
        entry_lines.append("")
    
    if changes.get("modified"):
        entry_lines.append(f"### Modified Chemicals ({len(changes['modified'])})")
        entry_lines.append("")
        for mod in changes["modified"]:
            cas = mod.get('cas_number', 'N/A')
            entry_lines.append(f"- CAS {cas}: Updated information")
        entry_lines.append("")
    
    if changes.get("threshold_changes"):
        entry_lines.append(f"### Threshold Changes ({len(changes['threshold_changes'])})")
        entry_lines.append("")
        for thresh in changes["threshold_changes"]:
            cas = thresh.get('cas_number', 'N/A')
            entry_lines.append(f"- CAS {cas}: NSRL/MADL values updated")
        entry_lines.append("")
    
    entry_lines.append("---")
    entry_lines.append("")
    
    # Prepend to existing content
    new_content = "\n".join(entry_lines) + "\n" + existing_content
    
    # Write back
    with open(changelog_file, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    return str(changelog_file)


def create_version_snapshot(
    source_dir: str,
    version_date: Optional[str] = None,
    output_dir: Optional[str] = None
) -> str:
    """
    Create a versioned snapshot of Prop 65 data
    
    Args:
        source_dir: Directory with current Prop 65 data
        version_date: Version date (YYYYMMDD format, None for current date)
        output_dir: Directory to save version snapshot
    
    Returns:
        Path to version snapshot directory
    """
    if output_dir is None:
        output_dir = os.getenv("EXTRACTED_DOCS_DIR", "./data/extracted_docs")
    
    if version_date is None:
        version_date = datetime.now().strftime("%Y%m%d")
    
    prop65_dir = Path(output_dir) / "compliance" / "prop65"
    versions_dir = prop65_dir / "versions"
    versions_dir.mkdir(parents=True, exist_ok=True)
    
    version_dir = versions_dir / version_date
    version_dir.mkdir(parents=True, exist_ok=True)
    
    source_path = Path(source_dir)
    
    # Copy key files
    files_to_copy = ["chemicals.md", "thresholds.md", "warning_rules.md"]
    
    for filename in files_to_copy:
        source_file = source_path / filename
        if source_file.exists():
            import shutil
            dest_file = version_dir / filename
            shutil.copy2(source_file, dest_file)
    
    # Create version metadata
    metadata = {
        "version_date": version_date,
        "created_at": datetime.now().isoformat(),
        "files": files_to_copy,
        "source": "OEHHA"
    }
    
    metadata_file = version_dir / "metadata.json"
    with open(metadata_file, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2)
    
    return str(version_dir)


def get_latest_version(
    versions_dir: Optional[str] = None
) -> Optional[str]:
    """
    Get the latest version date
    
    Args:
        versions_dir: Versions directory path
    
    Returns:
        Latest version date (YYYYMMDD) or None
    """
    if versions_dir is None:
        output_dir = os.getenv("EXTRACTED_DOCS_DIR", "./data/extracted_docs")
        versions_dir = str(Path(output_dir) / "compliance" / "prop65" / "versions")
    
    return _get_latest_version(Path(versions_dir))


def _get_latest_version(versions_dir: Path) -> Optional[str]:
    """Internal function to get latest version"""
    if not versions_dir.exists():
        return None
    
    version_dirs = [d.name for d in versions_dir.iterdir() if d.is_dir() and d.name.isdigit()]
    if not version_dirs:
        return None
    
    # Sort and return latest
    version_dirs.sort(reverse=True)
    return version_dirs[0]


def _parse_chemicals_file(file_path: Path) -> List[Dict[str, Any]]:
    """Parse chemicals.md file to extract chemical entries"""
    chemicals = []
    
    if not file_path.exists():
        return chemicals
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Parse frontmatter blocks
    import frontmatter
    
    # Split by frontmatter delimiters
    parts = content.split('---')
    
    for i in range(1, len(parts), 2):
        if i + 1 < len(parts):
            frontmatter_text = parts[i].strip()
            body_text = parts[i + 1] if i + 1 < len(parts) else ""
            
            try:
                post = frontmatter.loads(f"---\n{frontmatter_text}\n---\n{body_text}")
                chem = {
                    'cas_number': post.metadata.get('cas_number'),
                    'substance_name': post.metadata.get('substance_name'),
                    'toxicity_type': post.metadata.get('toxicity_type'),
                    'date_listed': post.metadata.get('date_listed'),
                    'nsrl': {
                        'value': post.metadata.get('nsrl_value'),
                        'unit': post.metadata.get('nsrl_unit')
                    } if post.metadata.get('nsrl_value') else None,
                    'madl': {
                        'value': post.metadata.get('madl_value'),
                        'unit': post.metadata.get('madl_unit')
                    } if post.metadata.get('madl_value') else None
                }
                chemicals.append(chem)
            except:
                continue
    
    return chemicals


def _parse_thresholds_file(file_path: Path) -> List[Dict[str, Any]]:
    """Parse thresholds.md file to extract threshold entries"""
    thresholds = []
    
    if not file_path.exists():
        return thresholds
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    import frontmatter
    
    parts = content.split('---')
    
    for i in range(1, len(parts), 2):
        if i + 1 < len(parts):
            frontmatter_text = parts[i].strip()
            
            try:
                post = frontmatter.loads(f"---\n{frontmatter_text}\n---\n")
                threshold = {
                    'cas_number': post.metadata.get('cas_number'),
                    'substance_name': post.metadata.get('substance_name'),
                    'nsrl': {
                        'value': post.metadata.get('nsrl_value'),
                        'unit': post.metadata.get('nsrl_unit')
                    } if post.metadata.get('nsrl_value') else None,
                    'madl': {
                        'value': post.metadata.get('madl_value'),
                        'unit': post.metadata.get('madl_unit')
                    } if post.metadata.get('madl_value') else None
                }
                thresholds.append(threshold)
            except:
                continue
    
    return thresholds

