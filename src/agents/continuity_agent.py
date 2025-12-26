"""Continuity Tracking Agent for maintaining consistency"""

import os
import json
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path

from ..bmad.agent_base import BaseAgent, AgentRole, AgentTool
from ..tools.model_manager import get_model_manager
from ..tools.llm_tools import call_llm

logger = logging.getLogger('continuity_agent')


class ContinuityAgent(BaseAgent):
    """Agent for tracking character, plot, and world-building consistency"""
    
    def __init__(self, framework=None):
        tools = [
            AgentTool(
                name="track_character",
                description="Track character details and consistency",
                func=self._track_character
            ),
            AgentTool(
                name="track_plot",
                description="Track plot threads and arcs",
                func=self._track_plot
            ),
            AgentTool(
                name="track_world",
                description="Track world-building elements",
                func=self._track_world
            ),
            AgentTool(
                name="check_consistency",
                description="Verify new content consistency",
                func=self._check_consistency
            )
        ]
        
        super().__init__(
            agent_id="continuity_agent",
            role=AgentRole.CONTINUITY,
            description="Tracks character, plot, and world-building consistency",
            tools=tools,
            framework=framework
        )
        
        self.model_manager = get_model_manager()
        self.consistency_db_path = os.path.join(
            os.getenv("EXTRACTED_DOCS_DIR", "./data/extracted_docs"),
            "writing",
            "consistency_db.json"
        )
        self.consistency_db: Dict[str, Dict] = {}
        self._load_consistency_db()
        
        self.logger = logging.getLogger(f"{self.agent_id}_logger")
        self.logger.setLevel(logging.INFO)
    
    def _load_consistency_db(self):
        """Load consistency database"""
        try:
            if os.path.exists(self.consistency_db_path):
                with open(self.consistency_db_path, 'r', encoding='utf-8') as f:
                    self.consistency_db = json.load(f)
        except Exception as e:
            self.logger.warning(f"Error loading consistency DB: {e}")
            self.consistency_db = {}
    
    def _save_consistency_db(self):
        """Save consistency database"""
        try:
            Path(self.consistency_db_path).parent.mkdir(parents=True, exist_ok=True)
            with open(self.consistency_db_path, 'w', encoding='utf-8') as f:
                json.dump(self.consistency_db, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"Error saving consistency DB: {e}", exc_info=True)
    
    def _track_character(self, project_id: str, character_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Track character details
        
        Args:
            project_id: Project ID
            character_data: Character information
            
        Returns:
            Tracking result
        """
        try:
            if project_id not in self.consistency_db:
                self.consistency_db[project_id] = {
                    'characters': {},
                    'locations': {},
                    'plot_points': []
                }
            
            char_name = character_data.get('name', 'Unknown')
            self.consistency_db[project_id]['characters'][char_name] = character_data
            self._save_consistency_db()
            
            return {
                'success': True,
                'character_tracked': char_name,
                'error': None
            }
            
        except Exception as e:
            self.logger.error(f"Error tracking character: {e}", exc_info=True)
            return {'success': False, 'error': str(e)}
    
    def _track_plot(self, project_id: str, plot_point: Dict[str, Any]) -> Dict[str, Any]:
        """
        Track plot threads
        
        Args:
            project_id: Project ID
            plot_point: Plot point information
            
        Returns:
            Tracking result
        """
        try:
            if project_id not in self.consistency_db:
                self.consistency_db[project_id] = {
                    'characters': {},
                    'locations': {},
                    'plot_points': []
                }
            
            self.consistency_db[project_id]['plot_points'].append(plot_point)
            self._save_consistency_db()
            
            return {
                'success': True,
                'plot_point_tracked': True,
                'error': None
            }
            
        except Exception as e:
            self.logger.error(f"Error tracking plot: {e}", exc_info=True)
            return {'success': False, 'error': str(e)}
    
    def _track_world(self, project_id: str, world_element: Dict[str, Any]) -> Dict[str, Any]:
        """
        Track world-building elements
        
        Args:
            project_id: Project ID
            world_element: World element information
            
        Returns:
            Tracking result
        """
        try:
            if project_id not in self.consistency_db:
                self.consistency_db[project_id] = {
                    'characters': {},
                    'locations': {},
                    'plot_points': []
                }
            
            element_name = world_element.get('name', 'Unknown')
            self.consistency_db[project_id]['locations'][element_name] = world_element
            self._save_consistency_db()
            
            return {
                'success': True,
                'world_element_tracked': element_name,
                'error': None
            }
            
        except Exception as e:
            self.logger.error(f"Error tracking world element: {e}", exc_info=True)
            return {'success': False, 'error': str(e)}
    
    def _check_consistency(self, project_id: str, new_content: str) -> Dict[str, Any]:
        """
        Verify new content consistency
        
        Args:
            project_id: Project ID
            new_content: New content to check
            
        Returns:
            Consistency check result
        """
        try:
            if project_id not in self.consistency_db:
                return {
                    'success': True,
                    'consistent': True,
                    'issues': [],
                    'warnings': []
                }
            
            project_data = self.consistency_db[project_id]
            issues = []
            warnings = []
            
            # Get model for continuity checking
            model_config = self.model_manager.get_model_for_task("continuity_checking")
            
            if model_config:
                # Use LLM to check consistency
                characters = project_data.get('characters', {})
                locations = project_data.get('locations', {})
                plot_points = project_data.get('plot_points', [])
                
                context = f"""Existing characters: {list(characters.keys())}
Existing locations: {list(locations.keys())}
Plot points: {len(plot_points)} tracked"""
                
                prompt = f"""Check if this new content is consistent with the existing story:

{context}

New content:
{new_content[:1000]}

Identify any inconsistencies with:
- Character descriptions or actions
- Location details
- Plot continuity
- World-building rules

List any issues found:"""
                
                model_name = model_config.get('model', 'llama3.2:1b')
                provider = model_config.get('provider', 'ollama')
                
                analysis = call_llm(
                    prompt=prompt,
                    model=model_name,
                    provider=provider,
                    max_tokens=500
                )
                
                # Parse issues from analysis (simplified)
                if 'inconsistent' in analysis.lower() or 'issue' in analysis.lower():
                    warnings.append(analysis)
            
            return {
                'success': True,
                'consistent': len(issues) == 0,
                'issues': issues,
                'warnings': warnings,
                'error': None
            }
            
        except Exception as e:
            self.logger.error(f"Error checking consistency: {e}", exc_info=True)
            return {'success': False, 'error': str(e)}
    
    def process(self, input_data: Any, **kwargs) -> Dict[str, Any]:
        """Process continuity tracking request"""
        if isinstance(input_data, dict):
            action = input_data.get('action', 'check')
            project_id = input_data.get('project_id', '')
            
            if action == 'track_character':
                return self._track_character(project_id, input_data.get('character_data', {}))
            elif action == 'track_plot':
                return self._track_plot(project_id, input_data.get('plot_point', {}))
            elif action == 'track_world':
                return self._track_world(project_id, input_data.get('world_element', {}))
            elif action == 'check':
                return self._check_consistency(project_id, input_data.get('new_content', ''))
            else:
                return {'success': False, 'error': f'Unknown action: {action}'}
        else:
            return {'success': False, 'error': 'Invalid input data'}

