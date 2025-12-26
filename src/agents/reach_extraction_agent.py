"""REACH Extraction Agent"""

from typing import Dict, List, Any, Optional
import os
from pathlib import Path

from ..bmad.agent_base import BaseAgent, AgentRole, AgentTool
from ..tools.reach_tools import (
    extract_echa_substances,
    extract_reach_regulation,
    extract_plastchem_data,
    normalize_chemical_name,
    validate_cas_number,
    validate_ec_number,
    extract_article_number
)


class REACHExtractionAgent(BaseAgent):
    """Agent for extracting REACH and chemical compliance data"""
    
    def __init__(self, framework=None):
        tools = [
            AgentTool(
                name="extract_echa_substances",
                description="Extract substance data from ECHA database",
                func=self._extract_echa_substances
            ),
            AgentTool(
                name="extract_reach_regulation",
                description="Extract REACH Regulation text from EUR-Lex",
                func=self._extract_reach_regulation
            ),
            AgentTool(
                name="extract_plastchem_data",
                description="Extract data from PlastChem database",
                func=self._extract_plastchem_data
            ),
            AgentTool(
                name="normalize_chemical_name",
                description="Normalize chemical name",
                func=self._normalize_chemical_name
            ),
            AgentTool(
                name="validate_cas_number",
                description="Validate CAS registry number format",
                func=self._validate_cas_number
            ),
            AgentTool(
                name="validate_ec_number",
                description="Validate EC number format",
                func=self._validate_ec_number
            ),
            AgentTool(
                name="extract_article_number",
                description="Extract REACH article number from text",
                func=self._extract_article_number
            )
        ]
        
        super().__init__(
            agent_id="reach_extraction_agent",
            role=AgentRole.REACH_EXTRACTION,
            description="Extracts REACH and chemical compliance data from various sources",
            tools=tools,
            framework=framework
        )
        
        self.extracted_files: List[str] = []
        self.extracted_substances: List[Dict] = []
        self.extracted_articles: List[Dict] = []
        self.extracted_plastchem: List[Dict] = []
    
    def _extract_echa_substances(self, output_dir: Optional[str] = None, limit: Optional[int] = None) -> List[Dict]:
        """Extract ECHA substances"""
        substances = extract_echa_substances(output_dir, limit)
        self.extracted_substances.extend(substances)
        return substances
    
    def _extract_reach_regulation(self, output_dir: Optional[str] = None, articles: Optional[List[str]] = None) -> List[Dict]:
        """Extract REACH regulation"""
        articles_data = extract_reach_regulation(output_dir, articles)
        self.extracted_articles.extend(articles_data)
        return articles_data
    
    def _extract_plastchem_data(self, output_dir: Optional[str] = None, source_path: Optional[str] = None) -> List[Dict]:
        """Extract PlastChem data"""
        chemicals = extract_plastchem_data(output_dir, source_path)
        self.extracted_plastchem.extend(chemicals)
        return chemicals
    
    def _normalize_chemical_name(self, name: str) -> str:
        """Normalize chemical name"""
        return normalize_chemical_name(name)
    
    def _validate_cas_number(self, cas_number: str) -> bool:
        """Validate CAS number"""
        return validate_cas_number(cas_number)
    
    def _validate_ec_number(self, ec_number: str) -> bool:
        """Validate EC number"""
        return validate_ec_number(ec_number)
    
    def _extract_article_number(self, text: str) -> Optional[str]:
        """Extract article number from text"""
        return extract_article_number(text)
    
    def process(self, input_data: Any, **kwargs) -> Dict[str, Any]:
        """
        Process REACH data extraction request
        
        Args:
            input_data: Dict with extraction parameters:
                - source: "echa", "reach_regulation", "plastchem", or "all"
                - output_dir: Output directory (optional)
                - articles: List of article numbers (for reach_regulation)
                - source_path: Path to source file (for plastchem)
                - limit: Maximum items to extract (for echa)
        """
        if isinstance(input_data, str):
            source = input_data
        elif isinstance(input_data, dict):
            source = input_data.get('source', 'all')
        else:
            return {"error": "Invalid input"}
        
        output_dir = kwargs.get('output_dir') or input_data.get('output_dir') if isinstance(input_data, dict) else None
        results = {
            "substances": [],
            "articles": [],
            "plastchem": []
        }
        
        try:
            if source in ['echa', 'all']:
                limit = kwargs.get('limit') or (input_data.get('limit') if isinstance(input_data, dict) else None)
                substances = self.execute_tool(
                    "extract_echa_substances",
                    output_dir=output_dir,
                    limit=limit
                )
                results["substances"] = substances
                self.extracted_files.extend([
                    f"substance_{s.get('cas_number', 'unknown')}.md"
                    for s in substances
                ])
            
            if source in ['reach_regulation', 'all']:
                articles = kwargs.get('articles') or (input_data.get('articles') if isinstance(input_data, dict) else None)
                articles_data = self.execute_tool(
                    "extract_reach_regulation",
                    output_dir=output_dir,
                    articles=articles
                )
                results["articles"] = articles_data
                self.extracted_files.extend([
                    f"article_{a.get('article_number', 'unknown').replace(' ', '_').lower()}.md"
                    for a in articles_data
                ])
            
            if source in ['plastchem', 'all']:
                source_path = kwargs.get('source_path') or (input_data.get('source_path') if isinstance(input_data, dict) else None)
                chemicals = self.execute_tool(
                    "extract_plastchem_data",
                    output_dir=output_dir,
                    source_path=source_path
                )
                results["plastchem"] = chemicals
                self.extracted_files.extend([
                    f"plastchem_{c.get('cas_number', 'unknown')}.md"
                    for c in chemicals
                ])
            
            # Notify document agent to process extracted files
            if self.framework and self.extracted_files:
                document_agent = self.framework.get_agent("document_agent")
                if document_agent:
                    # Get full paths
                    base_dir = output_dir or os.getenv("EXTRACTED_DOCS_DIR", "./data/extracted_docs")
                    file_paths = []
                    for filename in self.extracted_files:
                        # Try to find the file in various subdirectories
                        for subdir in ['reach_substances/registered_substances', 
                                      'reach_regulation/articles',
                                      'plastchem/hazardous_chemicals']:
                            full_path = Path(base_dir) / subdir / filename
                            if full_path.exists():
                                file_paths.append(str(full_path))
                                break
                    
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
                    {"type": "reach_extraction", "source": source}
                )
            
            return {
                "source": source,
                "files_extracted": len(self.extracted_files),
                "results": results
            }
            
        except Exception as e:
            return {
                "error": str(e),
                "source": source
            }

