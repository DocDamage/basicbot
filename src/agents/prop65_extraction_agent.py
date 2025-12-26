"""Prop 65 Extraction Agent"""

from typing import Dict, List, Any, Optional
import os
from pathlib import Path
from datetime import datetime

from ..bmad.agent_base import BaseAgent, AgentRole, AgentTool
from ..tools.prop65_tools import (
    extract_prop65_chemical_list,
    extract_nsrl_madl_thresholds,
    extract_warning_rules,
    download_oehha_data,
    normalize_prop65_entry,
    validate_prop65_listing,
    calculate_exposure_compliance,
    generate_warning_text
)
from ..tools.prop65_update_tools import (
    check_prop65_updates,
    compare_prop65_versions,
    create_prop65_changelog,
    create_version_snapshot,
    get_latest_version
)


class Prop65ExtractionAgent(BaseAgent):
    """Agent for extracting Prop 65 compliance data from OEHHA sources"""
    
    def __init__(self, framework=None):
        tools = [
            AgentTool(
                name="extract_prop65_chemical_list",
                description="Extract Prop 65 chemical list from OEHHA source",
                func=self._extract_prop65_chemical_list
            ),
            AgentTool(
                name="extract_nsrl_madl_thresholds",
                description="Extract NSRL and MADL threshold values",
                func=self._extract_nsrl_madl_thresholds
            ),
            AgentTool(
                name="extract_warning_rules",
                description="Extract warning language requirements",
                func=self._extract_warning_rules
            ),
            AgentTool(
                name="download_oehha_data",
                description="Download data from OEHHA website",
                func=self._download_oehha_data
            ),
            AgentTool(
                name="normalize_prop65_entry",
                description="Normalize Prop 65 chemical entry to standard format",
                func=self._normalize_prop65_entry
            ),
            AgentTool(
                name="validate_prop65_listing",
                description="Validate Prop 65 listing entry",
                func=self._validate_prop65_listing
            ),
            AgentTool(
                name="calculate_exposure_compliance",
                description="Check if exposure exceeds NSRL/MADL threshold",
                func=self._calculate_exposure_compliance
            ),
            AgentTool(
                name="generate_warning_text",
                description="Generate required Prop 65 warning text",
                func=self._generate_warning_text
            ),
            AgentTool(
                name="check_prop65_updates",
                description="Check for new Prop 65 updates from OEHHA",
                func=self._check_prop65_updates
            ),
            AgentTool(
                name="create_version_snapshot",
                description="Create a versioned snapshot of Prop 65 data",
                func=self._create_version_snapshot
            ),
            AgentTool(
                name="compare_prop65_versions",
                description="Compare two Prop 65 versions and identify changes",
                func=self._compare_prop65_versions
            )
        ]
        
        super().__init__(
            agent_id="prop65_extraction_agent",
            role=AgentRole.REACH_EXTRACTION,  # Reuse REACH_EXTRACTION role for now
            description="Extracts Prop 65 compliance data from OEHHA sources and manages version tracking",
            tools=tools,
            framework=framework
        )
        
        self.extracted_files: List[str] = []
        self.extracted_chemicals: List[Dict] = []
        self.extracted_thresholds: List[Dict] = []
        self.warning_rules: Dict[str, Any] = {}
    
    def _extract_prop65_chemical_list(
        self,
        source_path: Optional[str] = None,
        source_url: Optional[str] = None,
        output_dir: Optional[str] = None
    ) -> List[Dict]:
        """Extract Prop 65 chemical list"""
        chemicals = extract_prop65_chemical_list(source_path, source_url, output_dir)
        self.extracted_chemicals.extend(chemicals)
        return chemicals
    
    def _extract_nsrl_madl_thresholds(
        self,
        source_path: Optional[str] = None,
        source_url: Optional[str] = None,
        output_dir: Optional[str] = None
    ) -> List[Dict]:
        """Extract NSRL/MADL thresholds"""
        thresholds = extract_nsrl_madl_thresholds(source_path, source_url, output_dir)
        self.extracted_thresholds.extend(thresholds)
        return thresholds
    
    def _extract_warning_rules(
        self,
        source_path: Optional[str] = None,
        source_url: Optional[str] = None,
        output_dir: Optional[str] = None
    ) -> Dict[str, Any]:
        """Extract warning rules"""
        rules = extract_warning_rules(source_path, source_url, output_dir)
        self.warning_rules.update(rules)
        return rules
    
    def _download_oehha_data(
        self,
        url: str,
        output_path: Optional[str] = None,
        file_type: Optional[str] = None
    ) -> str:
        """Download OEHHA data"""
        return download_oehha_data(url, output_path, file_type)
    
    def _normalize_prop65_entry(self, entry: Dict[str, Any]) -> Optional[Dict]:
        """Normalize Prop 65 entry"""
        return normalize_prop65_entry(entry)
    
    def _validate_prop65_listing(self, entry: Dict[str, Any]) -> Dict[str, Any]:
        """Validate Prop 65 listing"""
        is_valid, errors = validate_prop65_listing(entry)
        return {
            "is_valid": is_valid,
            "errors": errors
        }
    
    def _calculate_exposure_compliance(
        self,
        cas_number: str,
        exposure_value: float,
        exposure_unit: str,
        threshold_type: str = "nsrl"
    ) -> Dict[str, Any]:
        """Calculate exposure compliance"""
        return calculate_exposure_compliance(cas_number, exposure_value, exposure_unit, threshold_type)
    
    def _generate_warning_text(
        self,
        cas_number: Optional[str] = None,
        substance_name: Optional[str] = None,
        warning_type: str = "consumer_product"
    ) -> str:
        """Generate warning text"""
        return generate_warning_text(cas_number, substance_name, warning_type)
    
    def _check_prop65_updates(
        self,
        current_version_dir: Optional[str] = None,
        oehha_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """Check for updates"""
        return check_prop65_updates(current_version_dir, oehha_url)
    
    def _create_version_snapshot(
        self,
        source_dir: str,
        version_date: Optional[str] = None,
        output_dir: Optional[str] = None
    ) -> str:
        """Create version snapshot"""
        return create_version_snapshot(source_dir, version_date, output_dir)
    
    def _compare_prop65_versions(
        self,
        version1_dir: str,
        version2_dir: str
    ) -> Dict[str, Any]:
        """Compare versions"""
        return compare_prop65_versions(version1_dir, version2_dir)
    
    def extract_from_file(
        self,
        file_path: str,
        data_type: str = "chemicals",
        output_dir: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Extract Prop 65 data from uploaded file
        
        Args:
            file_path: Path to source file
            data_type: Type of data ("chemicals", "thresholds", "warning_rules")
            output_dir: Output directory
        """
        if data_type == "chemicals":
            chemicals = self.execute_tool(
                "extract_prop65_chemical_list",
                source_path=file_path,
                output_dir=output_dir
            )
            return {"chemicals": chemicals, "count": len(chemicals)}
        
        elif data_type == "thresholds":
            thresholds = self.execute_tool(
                "extract_nsrl_madl_thresholds",
                source_path=file_path,
                output_dir=output_dir
            )
            return {"thresholds": thresholds, "count": len(thresholds)}
        
        elif data_type == "warning_rules":
            rules = self.execute_tool(
                "extract_warning_rules",
                source_path=file_path,
                output_dir=output_dir
            )
            return {"warning_rules": rules}
        
        else:
            return {"error": f"Unknown data type: {data_type}"}
    
    def extract_from_url(
        self,
        url: str,
        data_type: str = "chemicals",
        output_dir: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Download and extract Prop 65 data from OEHHA URL
        
        Args:
            url: OEHHA URL
            data_type: Type of data ("chemicals", "thresholds", "warning_rules")
            output_dir: Output directory
        """
        if data_type == "chemicals":
            chemicals = self.execute_tool(
                "extract_prop65_chemical_list",
                source_url=url,
                output_dir=output_dir
            )
            return {"chemicals": chemicals, "count": len(chemicals)}
        
        elif data_type == "thresholds":
            thresholds = self.execute_tool(
                "extract_nsrl_madl_thresholds",
                source_url=url,
                output_dir=output_dir
            )
            return {"thresholds": thresholds, "count": len(thresholds)}
        
        elif data_type == "warning_rules":
            rules = self.execute_tool(
                "extract_warning_rules",
                source_url=url,
                output_dir=output_dir
            )
            return {"warning_rules": rules}
        
        else:
            return {"error": f"Unknown data type: {data_type}"}
    
    def update_changelog(
        self,
        changes: Dict[str, Any],
        output_dir: Optional[str] = None
    ) -> str:
        """
        Update changelog with version changes
        
        Args:
            changes: Changes dictionary from compare_prop65_versions
            output_dir: Output directory
        """
        from ..tools.prop65_update_tools import create_prop65_changelog
        return create_prop65_changelog(changes, output_dir)
    
    def process(self, input_data: Any, **kwargs) -> Dict[str, Any]:
        """
        Process Prop 65 data extraction request
        
        Args:
            input_data: Dict with extraction parameters:
                - action: "extract", "update", "compare", "snapshot"
                - source_path: Path to source file (for extract)
                - source_url: URL to download from (for extract)
                - data_type: "chemicals", "thresholds", "warning_rules", or "all"
                - version1_dir: First version directory (for compare)
                - version2_dir: Second version directory (for compare)
        """
        if isinstance(input_data, str):
            action = input_data
        elif isinstance(input_data, dict):
            action = input_data.get('action', 'extract')
        else:
            return {"error": "Invalid input"}
        
        output_dir = kwargs.get('output_dir') or (input_data.get('output_dir') if isinstance(input_data, dict) else None)
        
        try:
            if action == "extract":
                data_type = kwargs.get('data_type') or (input_data.get('data_type', 'all') if isinstance(input_data, dict) else 'all')
                source_path = kwargs.get('source_path') or (input_data.get('source_path') if isinstance(input_data, dict) else None)
                source_url = kwargs.get('source_url') or (input_data.get('source_url') if isinstance(input_data, dict) else None)
                
                results = {}
                
                if data_type in ['chemicals', 'all']:
                    chemicals = self.execute_tool(
                        "extract_prop65_chemical_list",
                        source_path=source_path,
                        source_url=source_url,
                        output_dir=output_dir
                    )
                    results["chemicals"] = chemicals
                    self.extracted_files.append("chemicals.md")
                
                if data_type in ['thresholds', 'all']:
                    thresholds = self.execute_tool(
                        "extract_nsrl_madl_thresholds",
                        source_path=source_path,
                        source_url=source_url,
                        output_dir=output_dir
                    )
                    results["thresholds"] = thresholds
                    self.extracted_files.append("thresholds.md")
                
                if data_type in ['warning_rules', 'all']:
                    rules = self.execute_tool(
                        "extract_warning_rules",
                        source_path=source_path,
                        source_url=source_url,
                        output_dir=output_dir
                    )
                    results["warning_rules"] = rules
                    self.extracted_files.append("warning_rules.md")
                
                # Create version snapshot
                if output_dir:
                    prop65_dir = Path(output_dir) / "compliance" / "prop65"
                    if prop65_dir.exists():
                        self.execute_tool(
                            "create_version_snapshot",
                            source_dir=str(prop65_dir),
                            output_dir=output_dir
                        )
                
                # Notify document agent to process extracted files
                if self.framework and self.extracted_files:
                    document_agent = self.framework.get_agent("document_agent")
                    if document_agent:
                        base_dir = output_dir or os.getenv("EXTRACTED_DOCS_DIR", "./data/extracted_docs")
                        file_paths = []
                        for filename in self.extracted_files:
                            full_path = Path(base_dir) / "compliance" / "prop65" / filename
                            if full_path.exists():
                                file_paths.append(str(full_path))
                        
                        if file_paths:
                            self.send_message(
                                "document_agent",
                                {
                                    "action": "process_files",
                                    "file_paths": file_paths
                                }
                            )
                
                # Store in memory
                if self.framework:
                    self.framework.memory.store(
                        self.agent_id,
                        results,
                        {"type": "prop65_extraction", "action": action}
                    )
                
                return {
                    "action": "extract",
                    "data_type": data_type,
                    "files_extracted": len(self.extracted_files),
                    "results": results
                }
            
            elif action == "update":
                # Check for updates and process if available
                update_status = self.execute_tool("check_prop65_updates")
                
                if update_status.get("update_available"):
                    # Process update
                    return self.process({"action": "extract", "data_type": "all"}, **kwargs)
                else:
                    return {
                        "action": "update",
                        "update_available": False,
                        "status": update_status
                    }
            
            elif action == "compare":
                version1_dir = kwargs.get('version1_dir') or (input_data.get('version1_dir') if isinstance(input_data, dict) else None)
                version2_dir = kwargs.get('version2_dir') or (input_data.get('version2_dir') if isinstance(input_data, dict) else None)
                
                if not version1_dir or not version2_dir:
                    return {"error": "version1_dir and version2_dir required for compare"}
                
                changes = self.execute_tool(
                    "compare_prop65_versions",
                    version1_dir=version1_dir,
                    version2_dir=version2_dir
                )
                
                # Create changelog entry
                changelog_path = self.update_changelog(changes, output_dir)
                
                return {
                    "action": "compare",
                    "changes": changes,
                    "changelog": changelog_path
                }
            
            elif action == "snapshot":
                source_dir = kwargs.get('source_dir') or (input_data.get('source_dir') if isinstance(input_data, dict) else None)
                version_date = kwargs.get('version_date') or (input_data.get('version_date') if isinstance(input_data, dict) else None)
                
                if not source_dir:
                    # Use current prop65 directory
                    base_dir = output_dir or os.getenv("EXTRACTED_DOCS_DIR", "./data/extracted_docs")
                    source_dir = str(Path(base_dir) / "compliance" / "prop65")
                
                snapshot_path = self.execute_tool(
                    "create_version_snapshot",
                    source_dir=source_dir,
                    version_date=version_date,
                    output_dir=output_dir
                )
                
                return {
                    "action": "snapshot",
                    "snapshot_path": snapshot_path
                }
            
            else:
                return {"error": f"Unknown action: {action}"}
        
        except Exception as e:
            return {
                "error": str(e),
                "action": action
            }

