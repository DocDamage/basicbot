"""Writing Interface GUI Component"""

import customtkinter as ctk
from typing import Optional, Dict, Any, Callable
import os
from ..tools.model_manager import get_model_manager


class WritingInterface(ctk.CTkToplevel):
    """Writing interface window for book generation"""
    
    def __init__(self, parent, framework=None):
        super().__init__(parent)
        
        self.framework = framework
        self.current_project_id = None
        self.model_manager = get_model_manager()
        
        self.title("Writing Interface")
        self.geometry("1200x800")
        
        self._create_widgets()
    
    def _create_widgets(self):
        """Create GUI widgets"""
        # Main container
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        # Header with controls
        self.header_frame = ctk.CTkFrame(self)
        self.header_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=5)
        self.header_frame.grid_columnconfigure(1, weight=1)
        
        # Project selection
        ctk.CTkLabel(self.header_frame, text="Project:").grid(row=0, column=0, padx=5, pady=5)
        self.project_combo = ctk.CTkComboBox(
            self.header_frame,
            values=["New Project"],
            width=200,
            command=self._on_project_change
        )
        self.project_combo.set("New Project")
        self.project_combo.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        
        # New project button
        self.new_project_btn = ctk.CTkButton(
            self.header_frame,
            text="New Project",
            command=self._create_new_project,
            width=120
        )
        self.new_project_btn.grid(row=0, column=2, padx=5, pady=5)
        
        # Style reference
        ctk.CTkLabel(self.header_frame, text="Style Reference:").grid(row=1, column=0, padx=5, pady=5)
        self.style_entry = ctk.CTkEntry(
            self.header_frame,
            placeholder_text="Author name or book ID...",
            width=200
        )
        self.style_entry.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        
        # Generate button
        self.generate_btn = ctk.CTkButton(
            self.header_frame,
            text="Generate",
            command=self._generate_content,
            width=120
        )
        self.generate_btn.grid(row=1, column=2, padx=5, pady=5)
        
        # Main content area
        self.content_frame = ctk.CTkFrame(self)
        self.content_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        self.content_frame.grid_columnconfigure(0, weight=1)
        self.content_frame.grid_rowconfigure(0, weight=1)
        
        # Tab view for different writing modes
        self.tabview = ctk.CTkTabview(self.content_frame)
        self.tabview.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        
        # Outline tab
        self.outline_tab = self.tabview.add("Outline")
        self.outline_text = ctk.CTkTextbox(self.outline_tab, wrap="word", font=("Arial", 11))
        self.outline_text.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Chapter tab
        self.chapter_tab = self.tabview.add("Chapter")
        self.chapter_text = ctk.CTkTextbox(self.chapter_tab, wrap="word", font=("Arial", 11))
        self.chapter_text.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Full Book tab
        self.book_tab = self.tabview.add("Full Book")
        self.book_text = ctk.CTkTextbox(self.book_tab, wrap="word", font=("Arial", 11))
        self.book_text.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Settings tab
        self.settings_tab = self.tabview.add("Settings")
        self._create_settings_tab()
        
        # Footer with status
        self.footer_frame = ctk.CTkFrame(self)
        self.footer_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=5)
        self.footer_frame.grid_columnconfigure(0, weight=1)
        
        self.status_label = ctk.CTkLabel(
            self.footer_frame,
            text="Ready",
            font=("Arial", 10)
        )
        self.status_label.pack(side="left", padx=10, pady=5)
        
        # Export button
        self.export_btn = ctk.CTkButton(
            self.footer_frame,
            text="Export",
            command=self._export_content,
            width=100
        )
        self.export_btn.pack(side="right", padx=10, pady=5)
    
    def _create_settings_tab(self):
        """Create settings tab content"""
        # Generation settings
        ctk.CTkLabel(
            self.settings_tab,
            text="Generation Settings",
            font=("Arial", 14, "bold")
        ).pack(pady=10)
        
        # Structure type
        ctk.CTkLabel(self.settings_tab, text="Story Structure:").pack(pady=5)
        self.structure_combo = ctk.CTkComboBox(
            self.settings_tab,
            values=["3-act", "Hero's Journey", "Five Act", "Freytag's Pyramid"],
            width=200
        )
        self.structure_combo.set("3-act")
        self.structure_combo.pack(pady=5)
        
        # Output quality
        ctk.CTkLabel(self.settings_tab, text="Output Quality:").pack(pady=5)
        self.quality_combo = ctk.CTkComboBox(
            self.settings_tab,
            values=["Draft", "Polished", "Publication Ready"],
            width=200
        )
        self.quality_combo.set("Polished")
        self.quality_combo.pack(pady=5)
    
    def _create_new_project(self):
        """Create a new writing project"""
        dialog = ctk.CTkInputDialog(
            text="Enter project name:",
            title="New Project"
        )
        project_name = dialog.get_input()
        
        if project_name and self.framework:
            project_agent = self.framework.get_agent("project_agent")
            if project_agent:
                result = project_agent.execute_tool(
                    "create_project",
                    project_name=project_name
                )
                if result.get('success'):
                    self.current_project_id = result.get('project_id')
                    self.status_label.configure(text=f"Created project: {project_name}")
    
    def _on_project_change(self, value: str):
        """Handle project selection change"""
        if value != "New Project" and self.framework:
            # Load project
            project_agent = self.framework.get_agent("project_agent")
            if project_agent:
                # TODO: Implement project loading from selection
                # Would need to maintain project_id -> project_name mapping
                # For now, project selection is informational only
                logger.debug(f"Project selection changed to: {value}")
    
    def _generate_content(self):
        """Generate writing content"""
        if not self.framework:
            self.status_label.configure(text="Error: Framework not available")
            return
        
        writing_agent = self.framework.get_agent("writing_agent")
        if not writing_agent:
            self.status_label.configure(text="Error: Writing agent not found")
            return
        
        # Get prompt from current tab
        current_tab = self.tabview.get()
        style_reference = self.style_entry.get().strip() or None
        
        if current_tab == "Outline":
            # Generate outline
            prompt = self.outline_text.get("1.0", "end-1c").strip()
            if not prompt:
                prompt = "A story about adventure and discovery"
                self.outline_text.insert("1.0", prompt)
            
            self.status_label.configure(text="Generating outline...")
            result = writing_agent.execute_tool(
                "generate_outline",
                prompt=prompt,
                style_reference=style_reference,
                structure_type=self.structure_combo.get()
            )
            
            if result.get('success'):
                outline = result.get('outline', {})
                outline_text = outline.get('outline_text', '')
                self.outline_text.delete("1.0", "end")
                self.outline_text.insert("1.0", outline_text)
                self.status_label.configure(text="Outline generated successfully")
            else:
                self.status_label.configure(text=f"Error: {result.get('error')}")
        
        elif current_tab == "Chapter":
            # Generate chapter
            prompt = self.chapter_text.get("1.0", "end-1c").strip()
            if not prompt:
                prompt = "Chapter 1: The beginning of an adventure"
                self.chapter_text.insert("1.0", prompt)
            
            self.status_label.configure(text="Generating chapter...")
            result = writing_agent.execute_tool(
                "generate_chapter",
                chapter_prompt=prompt,
                project_id=self.current_project_id,
                chapter_number=1,
                style_reference=style_reference
            )
            
            if result.get('success'):
                chapter = result.get('chapter', {})
                chapter_text = chapter.get('chapter_text', '')
                self.chapter_text.delete("1.0", "end")
                self.chapter_text.insert("1.0", chapter_text)
                self.status_label.configure(text="Chapter generated successfully")
            else:
                self.status_label.configure(text=f"Error: {result.get('error')}")
        
        elif current_tab == "Full Book":
            # Generate full book (would need outline first)
            self.status_label.configure(text="Full book generation - use outline first")
    
    def _export_content(self):
        """Export generated content"""
        current_tab = self.tabview.get()
        
        if current_tab == "Outline":
            content = self.outline_text.get("1.0", "end-1c")
        elif current_tab == "Chapter":
            content = self.chapter_text.get("1.0", "end-1c")
        elif current_tab == "Full Book":
            content = self.book_text.get("1.0", "end-1c")
        else:
            return
        
        if not content.strip():
            self.status_label.configure(text="No content to export")
            return
        
        # Export dialog
        dialog = ctk.CTkInputDialog(
            text="Enter filename (without extension):",
            title="Export"
        )
        filename = dialog.get_input()
        
        if filename and self.framework:
            writing_agent = self.framework.get_agent("writing_agent")
            if writing_agent:
                metadata = {
                    'title': filename,
                    'author': 'AI Generated',
                    'created_at': '2024-01-01'
                }
                
                result = writing_agent.execute_tool(
                    "export_book",
                    book_content=content,
                    metadata=metadata,
                    format="markdown"
                )
                
                if result.get('success'):
                    self.status_label.configure(text=f"Exported to {result.get('output_path')}")
                else:
                    self.status_label.configure(text=f"Export error: {result.get('error')}")

