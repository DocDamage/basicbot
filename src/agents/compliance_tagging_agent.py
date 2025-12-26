"""Compliance Tagging Agent"""

from typing import Dict, List, Any, Optional
import os
from pathlib import Path

from ..bmad.agent_base import BaseAgent, AgentRole, AgentTool
from ..tools.compliance_tools import (
    tag_compliance_metadata,
    link_substance_to_regulation,
    extract_hazard_classification,
    normalize_chemical_identifier,
    extract_compliance_tags_from_text,
    validate_compliance_metadata,
    validate_prop65_metadata
)


class ComplianceTaggingAgent(BaseAgent):
    """Agent for tagging documents with compliance metadata"""
    
    def __init__(self, framework=None):
        tools = [
            AgentTool(
                name="tag_compliance_metadata",
                description="Add compliance metadata tags to a markdown file",
                func=self._tag_compliance_metadata
            ),
            AgentTool(
                name="link_substance_to_regulation",
                description="Create a link between a substance and a regulation",
                func=self._link_substance_to_regulation
            ),
            AgentTool(
                name="extract_hazard_classification",
                description="Extract hazard classifications from text",
                func=self._extract_hazard_classification
            ),
            AgentTool(
                name="normalize_chemical_identifier",
                description="Normalize chemical identifier (CAS or EC number)",
                func=self._normalize_chemical_identifier
            ),
            AgentTool(
                name="extract_compliance_tags_from_text",
                description="Extract compliance-related tags from text",
                func=self._extract_compliance_tags_from_text
            ),
            AgentTool(
                name="validate_compliance_metadata",
                description="Validate compliance metadata against schema",
                func=self._validate_compliance_metadata
            ),
            AgentTool(
                name="validate_prop65_metadata",
                description="Validate Prop 65 specific metadata",
                func=self._validate_prop65_metadata
            )
        ]
        
        super().__init__(
            agent_id="compliance_tagging_agent",
            role=AgentRole.COMPLIANCE_TAGGING,
            description="Tags documents with compliance metadata and validates chemical identifiers",
            tools=tools,
            framework=framework
        )
        
        self.tagged_files: List[str] = []
        self.validation_results: Dict[str, Dict] = {}
    
    def _tag_compliance_metadata(
        self,
        file_path: str,
        metadata: Dict[str, Any],
        schema_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """Tag file with compliance metadata"""
        result = tag_compliance_metadata(file_path, metadata, schema_path)
        if file_path not in self.tagged_files:
            self.tagged_files.append(file_path)
        return result
    
    def _link_substance_to_regulation(
        self,
        substance_file: str,
        regulation_file: str,
        link_type: str = "regulated_by"
    ) -> Dict[str, Any]:
        """Link substance to regulation"""
        return link_substance_to_regulation(substance_file, regulation_file, link_type)
    
    def _extract_hazard_classification(
        self,
        text: str,
        source: str = "REACH"
    ) -> List[str]:
        """Extract hazard classifications"""
        return extract_hazard_classification(text, source)
    
    def _normalize_chemical_identifier(
        self,
        identifier: str,
        identifier_type: str = "cas"
    ) -> Optional[str]:
        """Normalize chemical identifier"""
        return normalize_chemical_identifier(identifier, identifier_type)
    
    def _extract_compliance_tags_from_text(self, text: str) -> Dict[str, Any]:
        """Extract compliance tags from text"""
        return extract_compliance_tags_from_text(text)
    
    def _validate_compliance_metadata(
        self,
        metadata: Dict[str, Any],
        schema_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """Validate compliance metadata"""
        is_valid, errors = validate_compliance_metadata(metadata, schema_path)
        return {
            "is_valid": is_valid,
            "errors": errors
        }
    
    def _validate_prop65_metadata(
        self,
        metadata: Dict[str, Any],
        schema_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """Validate Prop 65 metadata"""
        is_valid, errors = validate_prop65_metadata(metadata, schema_path)
        return {
            "is_valid": is_valid,
            "errors": errors
        }
    
    def process(self, input_data: Any, **kwargs) -> Dict[str, Any]:
        """
        Process compliance tagging request
        
        Args:
            input_data: Dict with:
                - file_path: Path to file to tag
                - metadata: Metadata dictionary to add
                - action: "tag", "validate", "extract_tags", or "link"
                - For "link": substance_file, regulation_file, link_type
                - For "extract_tags": text
        """
        if isinstance(input_data, str):
            # Assume it's a file path, try to extract tags from it
            file_path = input_data
            action = "extract_tags"
        elif isinstance(input_data, dict):
            file_path = input_data.get('file_path')
            action = input_data.get('action', 'tag')
        else:
            return {"error": "Invalid input"}
        
        try:
            if action == "tag":
                metadata = kwargs.get('metadata') or input_data.get('metadata', {})
                schema_path = kwargs.get('schema_path') or input_data.get('schema_path')
                
                if not file_path:
                    return {"error": "file_path required for tagging"}
                
                result = self.execute_tool(
                    "tag_compliance_metadata",
                    file_path=file_path,
                    metadata=metadata,
                    schema_path=schema_path
                )
                
                return {
                    "action": "tag",
                    "file_path": file_path,
                    "metadata": result
                }
            
            elif action == "validate":
                metadata = kwargs.get('metadata') or input_data.get('metadata', {})
                schema_path = kwargs.get('schema_path') or input_data.get('schema_path')
                
                validation_result = self.execute_tool(
                    "validate_compliance_metadata",
                    metadata=metadata,
                    schema_path=schema_path
                )
                
                if file_path:
                    self.validation_results[file_path] = validation_result
                
                return {
                    "action": "validate",
                    "file_path": file_path,
                    "validation": validation_result
                }
            
            elif action == "extract_tags":
                if file_path and os.path.exists(file_path):
                    # Read file and extract tags from content
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    tags = self.execute_tool("extract_compliance_tags_from_text", text=content)
                    
                    # Also try to extract from metadata if it's a markdown file
                    try:
                        import frontmatter
                        post = frontmatter.loads(content)
                        if post.metadata:
                            # Extract additional tags from metadata
                            if 'cas_number' in post.metadata:
                                tags['cas_numbers'].append(post.metadata['cas_number'])
                            if 'ec_number' in post.metadata:
                                tags['ec_numbers'].append(post.metadata['ec_number'])
                            if 'article_number' in post.metadata:
                                tags['article_numbers'].append(post.metadata['article_number'])
                    except:
                        pass
                    
                    return {
                        "action": "extract_tags",
                        "file_path": file_path,
                        "tags": tags
                    }
                elif 'text' in input_data:
                    text = input_data['text']
                    tags = self.execute_tool("extract_compliance_tags_from_text", text=text)
                    return {
                        "action": "extract_tags",
                        "tags": tags
                    }
                else:
                    return {"error": "file_path or text required for extract_tags"}
            
            elif action == "link":
                substance_file = kwargs.get('substance_file') or input_data.get('substance_file')
                regulation_file = kwargs.get('regulation_file') or input_data.get('regulation_file')
                link_type = kwargs.get('link_type') or input_data.get('link_type', 'regulated_by')
                
                if not substance_file or not regulation_file:
                    return {"error": "substance_file and regulation_file required for linking"}
                
                result = self.execute_tool(
                    "link_substance_to_regulation",
                    substance_file=substance_file,
                    regulation_file=regulation_file,
                    link_type=link_type
                )
                
                return {
                    "action": "link",
                    "link": result
                }
            
            else:
                return {"error": f"Unknown action: {action}"}
        
        except Exception as e:
            return {
                "error": str(e),
                "action": action
            }
    
    def receive_message(self, from_agent_id: str, message: Any, metadata: Optional[Dict] = None):
        """Handle messages from other agents"""
        if isinstance(message, dict):
            action = message.get('action')
            
            if action == 'tag_file':
                # Tag a file that was just created/updated
                file_path = message.get('file_path')
                file_metadata = message.get('metadata', {})
                
                if file_path:
                    self.process({
                        'action': 'tag',
                        'file_path': file_path,
                        'metadata': file_metadata
                    })
            
            elif action == 'validate_file':
                # Validate metadata for a file
                file_path = message.get('file_path')
                file_metadata = message.get('metadata', {})
                
                if file_path:
                    self.process({
                        'action': 'validate',
                        'file_path': file_path,
                        'metadata': file_metadata
                    })

