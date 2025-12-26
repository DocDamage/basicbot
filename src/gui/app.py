"""Main GUI Application using CustomTkinter"""

import customtkinter as ctk
from typing import Optional, Dict, Any
import threading
import sys
import logging

from ..bmad.agent_base import BaseAgent, AgentRole
from ..config import get_settings

logger = logging.getLogger('gui_app')


class ChatApp(ctk.CTk):
    """Main chat application window"""
    
    def __init__(self, framework=None):
        super().__init__()
        
        self.framework = framework
        self.settings = get_settings()
        
        # Configure window
        self.title("RAG Chatbot - BMAD Framework")
        self.geometry("1200x800")
        
        # Configure appearance
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # Create main layout
        self._create_widgets()
        
        # Connect to framework
        if self.framework:
            self.gui_agent = framework.get_agent("gui_agent")
        else:
            self.gui_agent = None
    
    def _create_widgets(self):
        """Create GUI widgets"""
        # Main container
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Sidebar
        self.sidebar = ctk.CTkFrame(self, width=200)
        self.sidebar.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        
        # Settings button
        self.settings_btn = ctk.CTkButton(
            self.sidebar,
            text="Settings",
            command=self._open_settings
        )
        self.settings_btn.pack(pady=10, padx=10, fill="x")
        
        # Chat history button
        self.history_btn = ctk.CTkButton(
            self.sidebar,
            text="History",
            command=self._show_history
        )
        self.history_btn.pack(pady=10, padx=10, fill="x")
        
        # Books button
        self.books_btn = ctk.CTkButton(
            self.sidebar,
            text="Books",
            command=self._open_books
        )
        self.books_btn.pack(pady=10, padx=10, fill="x")
        
        # Writing button
        self.writing_btn = ctk.CTkButton(
            self.sidebar,
            text="Writing",
            command=self._open_writing
        )
        self.writing_btn.pack(pady=10, padx=10, fill="x")
        
        # Main chat area
        self.chat_frame = ctk.CTkFrame(self)
        self.chat_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        self.chat_frame.grid_columnconfigure(0, weight=1)
        self.chat_frame.grid_rowconfigure(0, weight=1)
        
        # Chat display
        self.chat_display = ctk.CTkTextbox(
            self.chat_frame,
            wrap="word",
            font=("Arial", 12)
        )
        self.chat_display.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        
        # Input area
        self.input_frame = ctk.CTkFrame(self.chat_frame)
        self.input_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=10)
        self.input_frame.grid_columnconfigure(0, weight=1)
        
        self.input_entry = ctk.CTkEntry(
            self.input_frame,
            placeholder_text="Type your question here...",
            font=("Arial", 12)
        )
        self.input_entry.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        self.input_entry.bind("<Return>", lambda e: self._send_message())
        
        self.send_btn = ctk.CTkButton(
            self.input_frame,
            text="Send",
            command=self._send_message,
            width=100
        )
        self.send_btn.grid(row=0, column=1)
    
    def _send_message(self):
        """Send user message"""
        query = self.input_entry.get()
        if not query.strip():
            return
        
        # Display user message
        self._add_message("user", query)
        self.input_entry.delete(0, "end")
        
        # Disable input during processing
        self.send_btn.configure(state="disabled")
        self.input_entry.configure(state="disabled")
        
        # Process in background thread
        thread = threading.Thread(target=self._process_query, args=(query,))
        thread.daemon = True
        thread.start()
    
    def _process_query(self, query: str):
        """Process query with framework (with streaming support)"""
        try:
            if self.framework:
                router_agent = self.framework.get_agent("router_agent")
                if router_agent:
                    # Get retrieval results first
                    retrieval_agent = self.framework.get_agent("retrieval_agent")
                    if retrieval_agent:
                        retrieval_result = retrieval_agent.process(
                            query,
                            strategy=self.settings.get_retrieval_strategy(),
                            top_k=self.settings.get("top_k", 5)
                        )
                        retrieval_results = retrieval_result.get("results", [])
                    else:
                        retrieval_results = []
                    
                    # Route to LLM with streaming
                    result = router_agent.process(
                        {"query": query, "retrieval_results": retrieval_results},
                        stream=True
                    )
                    
                    # Check if streaming
                    if "stream" in result:
                        # Start streaming response
                        self.after(0, lambda: self._start_streaming(result["stream"], retrieval_results))
                    else:
                        # Non-streaming response
                        response = result.get("response", "No response generated")
                        sources = [r.get("metadata", {}) for r in retrieval_results]
                        self.after(0, lambda: self._add_message("assistant", response, sources))
                        self.after(0, lambda: (
                            self.send_btn.configure(state="normal"),
                            self.input_entry.configure(state="normal")
                        ))
                else:
                    self.after(0, lambda: self._add_message("assistant", "Error: Router agent not found"))
                    self.after(0, lambda: (
                        self.send_btn.configure(state="normal"),
                        self.input_entry.configure(state="normal")
                    ))
            else:
                self.after(0, lambda: self._add_message("assistant", "Error: Framework not initialized"))
                self.after(0, lambda: (
                    self.send_btn.configure(state="normal"),
                    self.input_entry.configure(state="normal")
                ))
        except Exception as e:
            self.after(0, lambda: self._add_message("assistant", f"Error: {str(e)}"))
            self.after(0, lambda: (
                self.send_btn.configure(state="normal"),
                self.input_entry.configure(state="normal")
            ))
    
    def _start_streaming(self, stream, sources: list):
        """Start streaming response"""
        # Create placeholder for assistant message
        self.chat_display.insert("end", "ASSISTANT: ", "assistant")
        stream_start = self.chat_display.index("end-1c")
        self.chat_display.insert("end", "\n\n")
        
        # Start streaming in background thread
        def stream_response():
            full_text = ""
            try:
                for chunk_data in stream:
                    if isinstance(chunk_data, dict):
                        chunk = chunk_data.get("chunk", "")
                        full_text = chunk_data.get("full_response", full_text + chunk)
                    else:
                        chunk = str(chunk_data)
                        full_text += chunk
                    
                    if chunk:
                        # Update display
                        self.after(0, lambda c=chunk, ft=full_text: self._update_streaming(stream_start, ft))
                
                # Finalize with sources
                self.after(0, lambda: self._finalize_streaming(stream_start, full_text, sources))
            except Exception as e:
                self.after(0, lambda: self._finalize_streaming(stream_start, f"Error: {str(e)}", sources))
            finally:
                self.after(0, lambda: (
                    self.send_btn.configure(state="normal"),
                    self.input_entry.configure(state="normal")
                ))
        
        thread = threading.Thread(target=stream_response, daemon=True)
        thread.start()
    
    def _update_streaming(self, start_pos: str, text: str):
        """Update streaming text"""
        # Delete old content and insert new
        end_pos = self.chat_display.index("end-1c")
        self.chat_display.delete(start_pos, end_pos)
        self.chat_display.insert(start_pos, text)
        self.chat_display.see("end")
    
    def _finalize_streaming(self, start_pos: str, text: str, sources: list):
        """Finalize streaming response with sources"""
        # Update final text
        end_pos = self.chat_display.index("end-1c")
        self.chat_display.delete(start_pos, end_pos)
        self.chat_display.insert(start_pos, text)
        
        # Add sources
        if sources:
            self.chat_display.insert("end", "\n\nSources:\n", "sources_header")
            for i, source in enumerate(sources[:3], 1):
                source_file = source.get("source_file", "Unknown")
                source_path = source_file
                # Create clickable link
                self.chat_display.insert("end", f"  {i}. ", "source_num")
                self.chat_display.insert("end", source_path, ("source_link", f"source_{i}"))
                self.chat_display.insert("end", "\n")
                # Bind click event
                self.chat_display.tag_bind(f"source_{i}", "<Button-1>", 
                    lambda e, path=source_path: self._open_source_file(path))
        
        self.chat_display.insert("end", "\n\n")
        self.chat_display.see("end")
        
        # Configure text tags for styling
        self.chat_display.tag_config("sources_header", font=("Arial", 10, "bold"))
        self.chat_display.tag_config("source_link", foreground="#4A9EFF", underline=True)
        self.chat_display.tag_config("source_num", font=("Arial", 10))
    
    def _open_source_file(self, file_path: str) -> None:
        """
        Open source file in default system application
        
        Args:
            file_path: Path to file to open
            
        Note: Can be enhanced to open in editor or show preview
        """
        import os
        if os.path.exists(file_path):
            try:
                # Open file in default application
                if sys.platform == "win32":
                    os.startfile(file_path)
                elif sys.platform == "darwin":
                    os.system(f"open '{file_path}'")
                else:
                    os.system(f"xdg-open '{file_path}'")
            except Exception as e:
                logger.error(f"Error opening file {file_path}: {e}", exc_info=True)
    
    def _add_message(self, role: str, content: str, sources: Optional[list] = None):
        """Add message to chat display"""
        tag = "user" if role == "user" else "assistant"
        color = "#4A9EFF" if role == "user" else "#2B2B2B"
        
        self.chat_display.insert("end", f"{role.upper()}: ", tag)
        self.chat_display.insert("end", f"{content}\n\n")
        
        if sources and role == "assistant":
            self.chat_display.insert("end", "Sources:\n", "sources_header")
            for i, source in enumerate(sources[:3], 1):
                source_file = source.get("source_file", "Unknown")
                source_path = source_file
                # Create clickable link
                self.chat_display.insert("end", f"  {i}. ", "source_num")
                self.chat_display.insert("end", source_path, ("source_link", f"source_{i}"))
                self.chat_display.insert("end", "\n")
                # Bind click event
                self.chat_display.tag_bind(f"source_{i}", "<Button-1>", 
                    lambda e, path=source_path: self._open_source_file(path))
        
        # Configure text tags
        self.chat_display.tag_config("sources_header", font=("Arial", 10, "bold"))
        self.chat_display.tag_config("source_link", foreground="#4A9EFF", underline=True)
        self.chat_display.tag_config("source_num", font=("Arial", 10))
        
        self.chat_display.see("end")
    
    def _open_settings(self):
        """Open settings window"""
        settings_window = SettingsWindow(self, self.framework, self.settings)
        settings_window.grab_set()
    
    def _show_history(self):
        """Show chat history"""
        if self.framework:
            memory_agent = self.framework.get_agent("memory_agent")
            if memory_agent:
                history = memory_agent.process({"action": "get_history"})
                # Display history in a new window or in chat
                print("History:", history)
    
    def _open_books(self):
        """Open book browser"""
        from .book_browser import BookBrowser
        browser = BookBrowser(self, self.framework, on_book_select=self._open_book_reader)
    
    def _open_book_reader(self, book_id: str):
        """Open book in reader"""
        from .book_reader import BookReader
        reader = BookReader(self, self.framework, book_id)
    
    def _open_writing(self):
        """Open writing interface"""
        from .writing_interface import WritingInterface
        writing_window = WritingInterface(self, self.framework)


class SettingsWindow(ctk.CTkToplevel):
    """Settings configuration window"""
    
    def __init__(self, parent, framework, settings):
        super().__init__(parent)
        
        self.framework = framework
        self.settings = settings
        
        self.title("Settings")
        self.geometry("600x500")
        
        self._create_widgets()
    
    def _create_widgets(self):
        """Create settings widgets"""
        # Fast LLM selection
        ctk.CTkLabel(self, text="Fast LLM Model:").pack(pady=10)
        self.fast_llm_var = ctk.StringVar(value=self.settings.get("fast_llm.model", "llama3.2:1b"))
        fast_llm_menu = ctk.CTkOptionMenu(
            self,
            values=["llama3.2:1b", "llama3.2:3b", "phi3"],
            variable=self.fast_llm_var
        )
        fast_llm_menu.pack(pady=5)
        
        # Complex LLM selection
        ctk.CTkLabel(self, text="Complex LLM Model:").pack(pady=10)
        self.complex_llm_var = ctk.StringVar(value=self.settings.get("complex_llm.model", "mixtral:8x7b"))
        complex_llm_menu = ctk.CTkOptionMenu(
            self,
            values=["mixtral:8x7b", "mistral:7b"],
            variable=self.complex_llm_var
        )
        complex_llm_menu.pack(pady=5)
        
        # Save button
        save_btn = ctk.CTkButton(
            self,
            text="Save",
            command=self._save_settings
        )
        save_btn.pack(pady=20)
    
    def _save_settings(self):
        """Save settings"""
        self.settings.set("fast_llm.model", self.fast_llm_var.get())
        self.settings.set("complex_llm.model", self.complex_llm_var.get())
        self.destroy()

