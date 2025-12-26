"""Project Management Agent for writing projects"""

import os
import json
import logging
import shutil
from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime
import uuid

from ..bmad.agent_base import BaseAgent, AgentRole, AgentTool

logger = logging.getLogger('project_agent')


class ProjectAgent(BaseAgent):
    """Agent for managing writing projects, versions, and progress"""
    
    def __init__(self, framework=None):
        tools = [
            AgentTool(
                name="create_project",
                description="Create new writing project",
                func=self._create_project
            ),
            AgentTool(
                name="save_version",
                description="Save project version",
                func=self._save_version
            ),
            AgentTool(
                name="load_version",
                description="Load project version",
                func=self._load_version
            ),
            AgentTool(
                name="track_progress",
                description="Track writing progress",
                func=self._track_progress
            ),
            AgentTool(
                name="organize_workspace",
                description="Organize projects in workspaces",
                func=self._organize_workspace
            )
        ]
        
        super().__init__(
            agent_id="project_agent",
            role=AgentRole.PROJECT_MANAGEMENT,
            description="Manages writing projects, versions, and progress",
            tools=tools,
            framework=framework
        )
        
        self.projects_dir = os.path.join(
            os.getenv("EXTRACTED_DOCS_DIR", "./data/extracted_docs"),
            "writing",
            "projects"
        )
        os.makedirs(self.projects_dir, exist_ok=True)
        
        self.projects: Dict[str, Dict] = {}
        self._load_projects()
        
        self.logger = logging.getLogger(f"{self.agent_id}_logger")
        self.logger.setLevel(logging.INFO)
    
    def _load_projects(self):
        """Load all projects"""
        try:
            projects_file = os.path.join(self.projects_dir, "projects_index.json")
            if os.path.exists(projects_file):
                with open(projects_file, 'r', encoding='utf-8') as f:
                    self.projects = json.load(f)
        except Exception as e:
            self.logger.warning(f"Error loading projects: {e}")
            self.projects = {}
    
    def _save_projects_index(self):
        """Save projects index"""
        try:
            projects_file = os.path.join(self.projects_dir, "projects_index.json")
            with open(projects_file, 'w', encoding='utf-8') as f:
                json.dump(self.projects, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"Error saving projects index: {e}", exc_info=True)
    
    def _create_project(self, project_name: str, workspace: Optional[str] = None, 
                       metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Create new writing project
        
        Args:
            project_name: Project name
            workspace: Workspace name (optional)
            metadata: Additional metadata
            
        Returns:
            Project creation result
        """
        try:
            project_id = str(uuid.uuid4())
            
            # Create project directory
            if workspace:
                project_path = os.path.join(self.projects_dir, workspace, project_id)
            else:
                project_path = os.path.join(self.projects_dir, project_id)
            
            os.makedirs(project_path, exist_ok=True)
            
            # Create project data
            project_data = {
                'project_id': project_id,
                'project_name': project_name,
                'workspace': workspace,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat(),
                'versions': [],
                'current_version': None,
                'progress': {
                    'total_chapters': 0,
                    'completed_chapters': 0,
                    'word_count': 0
                },
                'metadata': metadata or {}
            }
            
            # Save project file
            project_file = os.path.join(project_path, "project.json")
            with open(project_file, 'w', encoding='utf-8') as f:
                json.dump(project_data, f, indent=2, ensure_ascii=False)
            
            # Add to index
            self.projects[project_id] = {
                'project_name': project_name,
                'workspace': workspace,
                'project_path': project_path,
                'created_at': project_data['created_at']
            }
            self._save_projects_index()
            
            return {
                'success': True,
                'project_id': project_id,
                'project_data': project_data,
                'error': None
            }
            
        except Exception as e:
            self.logger.error(f"Error creating project: {e}", exc_info=True)
            return {'success': False, 'error': str(e)}
    
    def _save_version(self, project_id: str, version_name: Optional[str] = None,
                     content: Optional[str] = None, metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Save project version
        
        Args:
            project_id: Project ID
            version_name: Version name (auto-generated if None)
            content: Project content
            metadata: Version metadata
            
        Returns:
            Version save result
        """
        try:
            # Load project
            project_file = os.path.join(self.projects_dir, self.projects[project_id]['project_path'], "project.json")
            if not os.path.exists(project_file):
                return {'success': False, 'error': 'Project not found'}
            
            with open(project_file, 'r', encoding='utf-8') as f:
                project_data = json.load(f)
            
            # Create version
            if not version_name:
                version_name = f"v{len(project_data.get('versions', [])) + 1}"
            
            version_id = str(uuid.uuid4())
            version_data = {
                'version_id': version_id,
                'version_name': version_name,
                'created_at': datetime.now().isoformat(),
                'metadata': metadata or {}
            }
            
            # Save version content if provided
            if content:
                version_file = os.path.join(
                    self.projects_dir,
                    self.projects[project_id]['project_path'],
                    "versions",
                    f"{version_id}.md"
                )
                os.makedirs(os.path.dirname(version_file), exist_ok=True)
                with open(version_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                version_data['content_file'] = version_file
            
            # Add to project
            if 'versions' not in project_data:
                project_data['versions'] = []
            project_data['versions'].append(version_data)
            project_data['current_version'] = version_id
            project_data['updated_at'] = datetime.now().isoformat()
            
            # Save project
            with open(project_file, 'w', encoding='utf-8') as f:
                json.dump(project_data, f, indent=2, ensure_ascii=False)
            
            return {
                'success': True,
                'version_id': version_id,
                'version_data': version_data,
                'error': None
            }
            
        except Exception as e:
            self.logger.error(f"Error saving version: {e}", exc_info=True)
            return {'success': False, 'error': str(e)}
    
    def _load_version(self, project_id: str, version_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Load project version
        
        Args:
            project_id: Project ID
            version_id: Version ID (loads current if None)
            
        Returns:
            Version data
        """
        try:
            project_file = os.path.join(self.projects_dir, self.projects[project_id]['project_path'], "project.json")
            if not os.path.exists(project_file):
                return {'success': False, 'error': 'Project not found'}
            
            with open(project_file, 'r', encoding='utf-8') as f:
                project_data = json.load(f)
            
            if not version_id:
                version_id = project_data.get('current_version')
            
            if not version_id:
                return {'success': False, 'error': 'No version specified'}
            
            # Find version
            version_data = None
            for version in project_data.get('versions', []):
                if version.get('version_id') == version_id:
                    version_data = version
                    break
            
            if not version_data:
                return {'success': False, 'error': 'Version not found'}
            
            # Load content if available
            content = None
            if version_data.get('content_file') and os.path.exists(version_data['content_file']):
                with open(version_data['content_file'], 'r', encoding='utf-8') as f:
                    content = f.read()
            
            return {
                'success': True,
                'version_data': version_data,
                'content': content,
                'error': None
            }
            
        except Exception as e:
            self.logger.error(f"Error loading version: {e}", exc_info=True)
            return {'success': False, 'error': str(e)}
    
    def _track_progress(self, project_id: str, progress_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Track writing progress
        
        Args:
            project_id: Project ID
            progress_data: Progress information
            
        Returns:
            Tracking result
        """
        try:
            project_file = os.path.join(self.projects_dir, self.projects[project_id]['project_path'], "project.json")
            if not os.path.exists(project_file):
                return {'success': False, 'error': 'Project not found'}
            
            with open(project_file, 'r', encoding='utf-8') as f:
                project_data = json.load(f)
            
            # Update progress
            if 'progress' not in project_data:
                project_data['progress'] = {}
            
            project_data['progress'].update(progress_data)
            project_data['updated_at'] = datetime.now().isoformat()
            
            # Save
            with open(project_file, 'w', encoding='utf-8') as f:
                json.dump(project_data, f, indent=2, ensure_ascii=False)
            
            return {
                'success': True,
                'progress': project_data['progress'],
                'error': None
            }
            
        except Exception as e:
            self.logger.error(f"Error tracking progress: {e}", exc_info=True)
            return {'success': False, 'error': str(e)}
    
    def _organize_workspace(self, workspace_name: str) -> Dict[str, Any]:
        """
        Organize projects in workspace
        
        Args:
            workspace_name: Workspace name
            
        Returns:
            Organization result
        """
        try:
            workspace_path = os.path.join(self.projects_dir, workspace_name)
            os.makedirs(workspace_path, exist_ok=True)
            
            # Find projects in workspace
            workspace_projects = [
                proj_id for proj_id, proj_data in self.projects.items()
                if proj_data.get('workspace') == workspace_name
            ]
            
            return {
                'success': True,
                'workspace': workspace_name,
                'workspace_path': workspace_path,
                'project_count': len(workspace_projects),
                'projects': workspace_projects,
                'error': None
            }
            
        except Exception as e:
            self.logger.error(f"Error organizing workspace: {e}", exc_info=True)
            return {'success': False, 'error': str(e)}
    
    def process(self, input_data: Any, **kwargs) -> Dict[str, Any]:
        """Process project management request"""
        if isinstance(input_data, dict):
            action = input_data.get('action', 'create')
            
            if action == 'create':
                return self._create_project(
                    input_data.get('project_name', 'Untitled'),
                    input_data.get('workspace'),
                    input_data.get('metadata')
                )
            elif action == 'save_version':
                return self._save_version(
                    input_data.get('project_id', ''),
                    input_data.get('version_name'),
                    input_data.get('content'),
                    input_data.get('metadata')
                )
            elif action == 'load_version':
                return self._load_version(
                    input_data.get('project_id', ''),
                    input_data.get('version_id')
                )
            elif action == 'track_progress':
                return self._track_progress(
                    input_data.get('project_id', ''),
                    input_data.get('progress_data', {})
                )
            elif action == 'organize':
                return self._organize_workspace(input_data.get('workspace_name', 'default'))
            else:
                return {'success': False, 'error': f'Unknown action: {action}'}
        else:
            return {'success': False, 'error': 'Invalid input data'}

