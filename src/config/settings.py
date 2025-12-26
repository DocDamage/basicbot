"""Configuration management"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional


class Settings:
    """Application settings manager"""
    
    def __init__(self, config_path: str = "./data/config.json"):
        self.config_path = Path(config_path)
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        self.settings: Dict[str, Any] = {}
        self.load()
    
    def load(self):
        """Load settings from file"""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    self.settings = json.load(f)
            except Exception as e:
                print(f"Error loading settings: {e}")
                self.settings = {}
        else:
            self.settings = self._default_settings()
            self.save()
    
    def save(self):
        """Save settings to file"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving settings: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a setting value"""
        keys = key.split('.')
        value = self.settings
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default
        return value if value is not None else default
    
    def set(self, key: str, value: Any):
        """Set a setting value"""
        keys = key.split('.')
        settings = self.settings
        for k in keys[:-1]:
            if k not in settings:
                settings[k] = {}
            settings = settings[k]
        settings[keys[-1]] = value
        self.save()
    
    def _default_settings(self) -> Dict[str, Any]:
        """Default settings"""
        ollama_endpoint = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        
        return {
            "fast_llm": {
                "provider": "ollama",
                "model": "llama3.2:1b",
                "endpoint": ollama_endpoint
            },
            "complex_llm": {
                "provider": "ollama",
                "model": "mixtral:8x7b",
                "endpoint": ollama_endpoint
            },
            "embedding_model": os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"),
            "retrieval_strategy": "hybrid",
            "chunk_size": 500,
            "chunk_overlap": 50,
            "top_k": 5,
            "zip_files": [],
            "llm_models": {
                "style_analysis": {
                    "provider": "ollama",
                    "model": "llama3.2:1b",
                    "format": "gguf",
                    "size": "small",
                    "endpoint": ollama_endpoint,
                    "fallback_models": ["phi-2", "tinyllama"],
                    "max_tokens": 512,
                    "temperature": 0.3
                },
                "text_generation": {
                    "provider": "ollama",
                    "model": "mistral:7b",
                    "format": "gguf",
                    "size": "medium",
                    "endpoint": ollama_endpoint,
                    "fallback_models": ["llama3.2:3b", "phi-2:2.7b"],
                    "max_tokens": 2048,
                    "temperature": 0.7
                },
                "character_tracking": {
                    "provider": "ollama",
                    "model": "llama3.2:3b",
                    "format": "gguf",
                    "size": "small",
                    "endpoint": ollama_endpoint,
                    "fallback_models": ["phi-2", "llama3.2:1b"],
                    "max_tokens": 1024,
                    "temperature": 0.2
                },
                "plot_development": {
                    "provider": "ollama",
                    "model": "mistral:7b",
                    "format": "gguf",
                    "size": "medium",
                    "endpoint": ollama_endpoint,
                    "fallback_models": ["llama3.2:3b", "neural-chat:7b"],
                    "max_tokens": 2048,
                    "temperature": 0.6
                },
                "continuity_checking": {
                    "provider": "ollama",
                    "model": "llama3.2:1b",
                    "format": "gguf",
                    "size": "small",
                    "endpoint": ollama_endpoint,
                    "fallback_models": ["tinyllama", "phi-2"],
                    "max_tokens": 512,
                    "temperature": 0.1
                },
                "refinement": {
                    "provider": "ollama",
                    "model": "mistral:7b",
                    "format": "gguf",
                    "size": "medium",
                    "endpoint": ollama_endpoint,
                    "fallback_models": ["llama3.2:3b", "neural-chat:7b"],
                    "max_tokens": 2048,
                    "temperature": 0.5
                },
                "outline_generation": {
                    "provider": "ollama",
                    "model": "llama3.2:3b",
                    "format": "gguf",
                    "size": "small",
                    "endpoint": ollama_endpoint,
                    "fallback_models": ["phi-2", "mistral:7b"],
                    "max_tokens": 1024,
                    "temperature": 0.4
                },
                "dialogue_generation": {
                    "provider": "ollama",
                    "model": "mistral:7b",
                    "format": "gguf",
                    "size": "medium",
                    "endpoint": ollama_endpoint,
                    "fallback_models": ["neural-chat:7b", "llama3.2:3b"],
                    "max_tokens": 1024,
                    "temperature": 0.8
                },
                "world_building": {
                    "provider": "ollama",
                    "model": "llama3.2:3b",
                    "format": "gguf",
                    "size": "small",
                    "endpoint": ollama_endpoint,
                    "fallback_models": ["phi-2", "mistral:7b"],
                    "max_tokens": 1536,
                    "temperature": 0.6
                }
            },
            "writing": {
                "output_quality": "polished",
                "generation_strategy": "all_strategies",
                "reference_usage": "automatic",
                "style_learning": "all_styles",
                "continuity_tracking": "all_consistency",
                "auto_save": {
                    "enabled": True,
                    "mode": "versioned",
                    "interval": "after_section"
                },
                "export_formats": ["markdown", "docx", "epub"],
                "project_management": {
                    "mode": "workspace",
                    "version_control": True,
                    "organize_by_workspace": True
                }
            },
            "model_management": {
                "auto_select": True,
                "lazy_loading": True,
                "max_concurrent_models": 3,
                "memory_limit_mb": 8192,
                "task_model_mapping": {
                    "style_analysis": "style_analysis",
                    "text_generation": "text_generation",
                    "character_tracking": "character_tracking",
                    "plot_development": "plot_development",
                    "continuity_checking": "continuity_checking",
                    "refinement": "refinement",
                    "outline_generation": "outline_generation",
                    "dialogue_generation": "dialogue_generation",
                    "world_building": "world_building"
                },
                "model_priorities": {
                    "high": ["text_generation", "refinement"],
                    "medium": ["plot_development", "dialogue_generation"],
                    "low": ["style_analysis", "continuity_checking", "character_tracking"]
                },
                "format_preferences": {
                    "primary": "gguf",
                    "fallback": "onnx",
                    "last_resort": "transformers"
                }
            },
            "book_reader": {
                "words_per_page": 500,
                "font_size": 12,
                "font_family": "Arial"
            },
            "writing": {
                "default_chapter_count": 10,
                "default_chapter_length": 2000
            }
        }
    
    def get_fast_llm_config(self) -> Dict[str, Any]:
        """Get fast LLM configuration"""
        return self.get("fast_llm", {})
    
    def get_complex_llm_config(self) -> Dict[str, Any]:
        """Get complex LLM configuration"""
        return self.get("complex_llm", {})
    
    def get_embedding_model(self) -> str:
        """Get embedding model name"""
        return self.get("embedding_model", "sentence-transformers/all-MiniLM-L6-v2")
    
    def get_retrieval_strategy(self) -> str:
        """Get retrieval strategy"""
        return self.get("retrieval_strategy", "hybrid")
    
    def get_writing_config(self) -> Dict[str, Any]:
        """Get writing configuration"""
        return self.get("writing", {})
    
    def get_model_management_config(self) -> Dict[str, Any]:
        """Get model management configuration"""
        return self.get("model_management", {})
    
    def get_llm_model_config(self, model_id: str) -> Dict[str, Any]:
        """Get configuration for a specific LLM model"""
        llm_models = self.get("llm_models", {})
        return llm_models.get(model_id, {})


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get global settings instance"""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings

