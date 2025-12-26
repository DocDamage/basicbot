"""Style Analysis Agent for analyzing writing styles"""

import os
import logging
from typing import Dict, List, Any, Optional

from ..bmad.agent_base import BaseAgent, AgentRole, AgentTool
from ..tools.model_manager import get_model_manager
from ..tools.llm_tools import call_llm
from ..tools.writing_tools import analyze_author_style, analyze_genre_style

logger = logging.getLogger('style_analysis_agent')


class StyleAnalysisAgent(BaseAgent):
    """Specialized agent for analyzing writing styles"""
    
    def __init__(self, framework=None):
        tools = [
            AgentTool(
                name="analyze_style",
                description="Analyze writing style from text",
                func=self._analyze_style
            ),
            AgentTool(
                name="compare_styles",
                description="Compare styles between authors/books",
                func=self._compare_styles
            ),
            AgentTool(
                name="extract_style_features",
                description="Extract style characteristics",
                func=self._extract_style_features
            )
        ]
        
        super().__init__(
            agent_id="style_analysis_agent",
            role=AgentRole.STYLE_ANALYSIS,
            description="Analyzes writing styles from books",
            tools=tools,
            framework=framework
        )
        
        self.model_manager = get_model_manager()
        self.logger = logging.getLogger(f"{self.agent_id}_logger")
        self.logger.setLevel(logging.INFO)
    
    def _analyze_style(self, text: str, reference: Optional[str] = None) -> Dict[str, Any]:
        """
        Analyze writing style from text
        
        Args:
            text: Text to analyze
            reference: Optional reference author/book for comparison
            
        Returns:
            Dictionary with style analysis
        """
        try:
            # Get model for style analysis
            model_config = self.model_manager.get_model_for_task("style_analysis")
            if not model_config:
                return {'success': False, 'error': 'No model configured for style analysis'}
            
            prompt = f"""Analyze the writing style of this text and provide detailed characteristics:

{text[:2000]}

Provide analysis of:
1. Sentence structure and length
2. Vocabulary and word choice
3. Tone and voice
4. Dialogue style
5. Narrative style
6. Pacing
"""
            
            model_name = model_config.get('model', 'llama3.2:1b')
            provider = model_config.get('provider', 'ollama')
            
            analysis_text = call_llm(
                prompt=prompt,
                model=model_name,
                provider=provider,
                max_tokens=1000
            )
            
            # Also get quantitative analysis
            if reference:
                style_data = analyze_author_style([], reference)
            else:
                style_data = {}
            
            return {
                'success': True,
                'analysis': analysis_text,
                'quantitative': style_data,
                'error': None
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing style: {e}", exc_info=True)
            return {'success': False, 'error': str(e)}
    
    def _compare_styles(self, style1: Dict[str, Any], style2: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compare styles between authors/books
        
        Args:
            style1: First style data
            style2: Second style data
            
        Returns:
            Dictionary with comparison
        """
        try:
            model_config = self.model_manager.get_model_for_task("style_analysis")
            if not model_config:
                return {'success': False, 'error': 'No model configured for style analysis'}
            
            prompt = f"""Compare these two writing styles and identify similarities and differences:

Style 1:
{style1}

Style 2:
{style2}

Provide a detailed comparison."""
            
            model_name = model_config.get('model', 'llama3.2:1b')
            provider = model_config.get('provider', 'ollama')
            
            comparison = call_llm(
                prompt=prompt,
                model=model_name,
                provider=provider,
                max_tokens=1000
            )
            
            return {
                'success': True,
                'comparison': comparison,
                'error': None
            }
            
        except Exception as e:
            self.logger.error(f"Error comparing styles: {e}", exc_info=True)
            return {'success': False, 'error': str(e)}
    
    def _extract_style_features(self, text: str) -> Dict[str, Any]:
        """
        Extract style characteristics
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary with style features
        """
        try:
            # Use quantitative analysis
            style_data = analyze_author_style([], None)
            
            # Also use LLM for qualitative features
            model_config = self.model_manager.get_model_for_task("style_analysis")
            if model_config:
                prompt = f"""Extract key style features from this text:

{text[:2000]}

List the most distinctive style features."""
                
                model_name = model_config.get('model', 'llama3.2:1b')
                provider = model_config.get('provider', 'ollama')
                
                features_text = call_llm(
                    prompt=prompt,
                    model=model_name,
                    provider=provider,
                    max_tokens=500
                )
                style_data['qualitative_features'] = features_text
            
            return {
                'success': True,
                'features': style_data,
                'error': None
            }
            
        except Exception as e:
            self.logger.error(f"Error extracting style features: {e}", exc_info=True)
            return {'success': False, 'error': str(e)}
    
    def process(self, input_data: Any, **kwargs) -> Dict[str, Any]:
        """Process style analysis request"""
        if isinstance(input_data, str):
            return self._analyze_style(input_data)
        elif isinstance(input_data, dict):
            action = input_data.get('action', 'analyze')
            if action == 'analyze':
                return self._analyze_style(input_data.get('text', ''), input_data.get('reference'))
            elif action == 'compare':
                return self._compare_styles(input_data.get('style1', {}), input_data.get('style2', {}))
            elif action == 'extract':
                return self._extract_style_features(input_data.get('text', ''))
            else:
                return {'success': False, 'error': f'Unknown action: {action}'}
        else:
            return {'success': False, 'error': 'Invalid input data'}

