"""Writing Agent for book generation using book collection as reference"""

import os
import logging
import uuid
from typing import Dict, List, Any, Optional
from datetime import datetime

from ..bmad.agent_base import BaseAgent, AgentRole, AgentTool
from ..tools.writing_tools import (
    analyze_author_style,
    analyze_genre_style,
    extract_story_structure,
    generate_character_sheet,
    track_continuity,
    refine_style,
    export_to_markdown,
    export_to_docx,
    export_to_epub
)
from ..tools.model_manager import get_model_manager
from ..tools.llm_tools import call_llm, stream_llm
from ..tools.book_retrieval_tools import search_by_author, search_by_genre, get_related_books
from ..config import get_settings

logger = logging.getLogger('writing_agent')


class WritingAgent(BaseAgent):
    """Agent for generating books using book collection as reference"""
    
    def __init__(self, framework=None):
        tools = [
            AgentTool(
                name="generate_outline",
                description="Generate story outline",
                func=self._generate_outline
            ),
            AgentTool(
                name="generate_chapter",
                description="Generate individual chapter",
                func=self._generate_chapter
            ),
            AgentTool(
                name="generate_full_book",
                description="Generate complete book",
                func=self._generate_full_book
            ),
            AgentTool(
                name="analyze_writing_style",
                description="Analyze writing style from reference books",
                func=self._analyze_writing_style
            ),
            AgentTool(
                name="extract_plot_patterns",
                description="Extract plot structures from books",
                func=self._extract_plot_patterns
            ),
            AgentTool(
                name="maintain_continuity",
                description="Track character/plot/world consistency",
                func=self._maintain_continuity
            ),
            AgentTool(
                name="refine_text",
                description="Edit and refine generated text",
                func=self._refine_text
            ),
            AgentTool(
                name="export_book",
                description="Export to Markdown/DOCX/EPUB",
                func=self._export_book
            )
        ]
        
        super().__init__(
            agent_id="writing_agent",
            role=AgentRole.WRITING,
            description="Generates books using book collection as reference",
            tools=tools,
            framework=framework
        )
        
        self.model_manager = get_model_manager()
        self.projects: Dict[str, Dict] = {}
        self.current_project: Optional[str] = None
        
        # Setup logging
        log_dir = os.getenv("LOG_DIR", "./data/logs")
        os.makedirs(log_dir, exist_ok=True)
        self.logger = logging.getLogger(f"{self.agent_id}_logger")
        self.logger.setLevel(logging.INFO)
    
    def _generate_outline(self, prompt: str, style_reference: Optional[str] = None, 
                         structure_type: str = "3-act") -> Dict[str, Any]:
        """
        Generate story outline
        
        Args:
            prompt: Story prompt/idea
            style_reference: Reference author or book ID
            structure_type: Story structure type (3-act, hero's journey, etc.)
            
        Returns:
            Dictionary with outline
        """
        try:
            # Get model for plot development
            model_config = self.model_manager.get_model_for_task("plot_development")
            if not model_config:
                return {'success': False, 'error': 'No model configured for plot development'}
            
            # Get reference style if provided
            style_context = ""
            if style_reference:
                style_data = self._analyze_writing_style(style_reference)
                if style_data.get('success'):
                    style_context = f"\n\nReference style: {style_data.get('style_characteristics', {})}"
            
            # Build prompt
            full_prompt = f"""Generate a {structure_type} story outline based on this idea:

{prompt}
{style_context}

Provide a detailed outline with:
1. Main characters and their arcs
2. Three-act structure breakdown
3. Key plot points
4. Major conflicts and resolutions
"""
            
            # Call LLM
            model_name = model_config.get('model', 'llama3.2:1b')
            provider = model_config.get('provider', 'ollama')
            endpoint = model_config.get('endpoint', 'http://localhost:11434')
            
            outline_text = call_llm(
                prompt=full_prompt,
                model=model_name,
                provider=provider,
                max_tokens=2000
            )
            
            outline = {
                'outline_id': str(uuid.uuid4()),
                'prompt': prompt,
                'structure_type': structure_type,
                'outline_text': outline_text,
                'created_at': datetime.now().isoformat()
            }
            
            return {
                'success': True,
                'outline': outline,
                'error': None
            }
            
        except Exception as e:
            self.logger.error(f"Error generating outline: {e}", exc_info=True)
            return {'success': False, 'error': str(e)}
    
    def _generate_chapter(self, chapter_prompt: str, project_id: Optional[str] = None,
                         chapter_number: int = 1, style_reference: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate individual chapter
        
        Args:
            chapter_prompt: Chapter description/prompt
            project_id: Project ID for context
            chapter_number: Chapter number
            style_reference: Reference author or book ID
            
        Returns:
            Dictionary with generated chapter
        """
        try:
            # Get model for text generation
            model_config = self.model_manager.get_model_for_task("text_generation")
            if not model_config:
                return {'success': False, 'error': 'No model configured for text generation'}
            
            # Get project context
            context = ""
            if project_id and project_id in self.projects:
                project = self.projects[project_id]
                context = f"\n\nPrevious context: {project.get('summary', '')}"
            
            # Get style reference
            style_context = ""
            if style_reference:
                style_data = self._analyze_writing_style(style_reference)
                if style_data.get('success'):
                    style_context = f"\n\nWriting style: Match the style of {style_reference}"
            
            # Build prompt
            full_prompt = f"""Write Chapter {chapter_number} of a book.

Chapter description: {chapter_prompt}
{context}
{style_context}

Write a complete, polished chapter that:
- Is engaging and well-written
- Matches the specified style
- Maintains consistency with previous chapters
- Is approximately 2000-3000 words
"""
            
            # Stream generation
            model_name = model_config.get('model', 'mistral:7b')
            provider = model_config.get('provider', 'ollama')
            
            chapter_text = ""
            for chunk in stream_llm(full_prompt, model=model_name, provider=provider):
                chapter_text += str(chunk)
            
            chapter = {
                'chapter_number': chapter_number,
                'chapter_text': chapter_text,
                'word_count': len(chapter_text.split()),
                'created_at': datetime.now().isoformat()
            }
            
            return {
                'success': True,
                'chapter': chapter,
                'error': None
            }
            
        except Exception as e:
            self.logger.error(f"Error generating chapter: {e}", exc_info=True)
            return {'success': False, 'error': str(e)}
    
    def _generate_full_book(self, outline: Dict[str, Any], style_reference: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate complete book from outline
        
        Args:
            outline: Story outline dictionary
            style_reference: Reference author or book ID
            
        Returns:
            Dictionary with generated book
        """
        try:
            chapters = []
            outline_text = outline.get('outline_text', '')
            
            # Parse outline to get chapter list (simplified)
            # In practice, would parse outline more intelligently
            settings = get_settings()
            chapter_count = settings.get("writing.default_chapter_count", 10)
            
            # Generate chapters with progress tracking
            for i in range(1, chapter_count + 1):
                self.logger.info(f"Generating chapter {i}/{chapter_count}...")
                chapter_prompt = f"Chapter {i} based on outline: {outline_text[:500]}"
                result = self._generate_chapter(chapter_prompt, chapter_number=i, style_reference=style_reference)
                if result.get('success'):
                    chapters.append(result.get('chapter'))
                else:
                    self.logger.warning(f"Failed to generate chapter {i}: {result.get('error')}")
            
            book_content = "\n\n".join([ch.get('chapter_text', '') for ch in chapters])
            
            book = {
                'book_id': str(uuid.uuid4()),
                'outline': outline,
                'chapters': chapters,
                'full_text': book_content,
                'total_words': sum(ch.get('word_count', 0) for ch in chapters),
                'created_at': datetime.now().isoformat()
            }
            
            return {
                'success': True,
                'book': book,
                'error': None
            }
            
        except Exception as e:
            self.logger.error(f"Error generating full book: {e}", exc_info=True)
            return {'success': False, 'error': str(e)}
    
    def _analyze_writing_style(self, reference: str) -> Dict[str, Any]:
        """
        Analyze writing style from reference books
        
        Args:
            reference: Author name or book ID
            
        Returns:
            Dictionary with style characteristics
        """
        try:
            # Try to find books by author
            author_books = search_by_author(reference, top_k=5)
            book_ids = [b.get('metadata', {}).get('book_id') for b in author_books 
                       if b.get('metadata', {}).get('book_id')]
            
            if not book_ids:
                # Try as book ID
                book_ids = [reference]
            
            style_data = analyze_author_style(book_ids, reference)
            
            return {
                'success': True,
                'style_characteristics': style_data,
                'error': None
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing writing style: {e}", exc_info=True)
            return {'success': False, 'error': str(e)}
    
    def _extract_plot_patterns(self, book_id: str) -> Dict[str, Any]:
        """Extract plot structures from a book"""
        try:
            structure = extract_story_structure(book_id)
            return {
                'success': True,
                'structure': structure,
                'error': None
            }
        except Exception as e:
            self.logger.error(f"Error extracting plot patterns: {e}", exc_info=True)
            return {'success': False, 'error': str(e)}
    
    def _maintain_continuity(self, project_id: str, new_content: str) -> Dict[str, Any]:
        """Track character/plot/world consistency"""
        try:
            # Get continuity agent if available
            if self.framework:
                continuity_agent = self.framework.get_agent("continuity_agent")
                if continuity_agent:
                    return continuity_agent.execute_tool("check_consistency", 
                                                        project_id=project_id, 
                                                        new_content=new_content)
            
            # Fallback: simple tracking
            if project_id not in self.projects:
                self.projects[project_id] = {
                    'characters': {},
                    'locations': {},
                    'plot_points': []
                }
            
            consistency_db = {project_id: self.projects[project_id]}
            result = track_continuity(project_id, new_content, consistency_db)
            
            return {
                'success': True,
                'consistency_check': result,
                'error': None
            }
            
        except Exception as e:
            self.logger.error(f"Error maintaining continuity: {e}", exc_info=True)
            return {'success': False, 'error': str(e)}
    
    def _refine_text(self, text: str, target_style: Optional[Dict] = None) -> Dict[str, Any]:
        """Edit and refine generated text"""
        try:
            # Get model for refinement
            model_config = self.model_manager.get_model_for_task("refinement")
            if not model_config:
                return {'success': False, 'error': 'No model configured for refinement'}
            
            prompt = f"""Refine and polish this text to make it more engaging and well-written:

{text}

Provide the refined version:"""
            
            model_name = model_config.get('model', 'mistral:7b')
            provider = model_config.get('provider', 'ollama')
            
            refined_text = call_llm(
                prompt=prompt,
                model=model_name,
                provider=provider,
                max_tokens=len(text.split()) * 2
            )
            
            return {
                'success': True,
                'original_text': text,
                'refined_text': refined_text,
                'error': None
            }
            
        except Exception as e:
            self.logger.error(f"Error refining text: {e}", exc_info=True)
            return {'success': False, 'error': str(e)}
    
    def _export_book(self, book_content: str, metadata: Dict[str, Any], 
                    format: str = "markdown", output_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Export book to file
        
        Args:
            book_content: Book content text
            metadata: Book metadata
            format: Export format (markdown, docx, epub)
            output_path: Output file path
            
        Returns:
            Dictionary with export result
        """
        try:
            if not output_path:
                output_dir = os.getenv("WRITING_OUTPUT_DIR", "./data/writing_output")
                os.makedirs(output_dir, exist_ok=True)
                title = metadata.get('title', 'untitled').replace(' ', '_')
                output_path = os.path.join(output_dir, f"{title}.{format}")
            
            success = False
            if format == "markdown":
                success = export_to_markdown(book_content, metadata, output_path)
            elif format == "docx":
                success = export_to_docx(book_content, metadata, output_path)
            elif format == "epub":
                success = export_to_epub(book_content, metadata, output_path)
            else:
                return {'success': False, 'error': f'Unsupported format: {format}'}
            
            return {
                'success': success,
                'output_path': output_path if success else None,
                'error': None if success else 'Export failed'
            }
            
        except Exception as e:
            self.logger.error(f"Error exporting book: {e}", exc_info=True)
            return {'success': False, 'error': str(e)}
    
    def process(self, input_data: Any, **kwargs) -> Dict[str, Any]:
        """
        Process writing request
        
        Args:
            input_data: Can be a prompt string or dict with writing parameters
            **kwargs: Additional parameters
            
        Returns:
            Writing result
        """
        if isinstance(input_data, str):
            # Simple prompt - generate outline
            return self._generate_outline(input_data)
        elif isinstance(input_data, dict):
            action = input_data.get('action', 'generate')
            
            if action == 'outline':
                return self._generate_outline(
                    input_data.get('prompt', ''),
                    input_data.get('style_reference'),
                    input_data.get('structure_type', '3-act')
                )
            elif action == 'chapter':
                return self._generate_chapter(
                    input_data.get('chapter_prompt', ''),
                    input_data.get('project_id'),
                    input_data.get('chapter_number', 1),
                    input_data.get('style_reference')
                )
            elif action == 'full_book':
                return self._generate_full_book(
                    input_data.get('outline', {}),
                    input_data.get('style_reference')
                )
            else:
                return {'success': False, 'error': f'Unknown action: {action}'}
        else:
            return {'success': False, 'error': 'Invalid input data'}

