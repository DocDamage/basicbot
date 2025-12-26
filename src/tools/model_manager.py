"""Model Manager for multiple LLM models"""

import os
import logging
from typing import Dict, List, Optional, Any
from ..config import get_settings

logger = logging.getLogger('model_manager')

# Try to import Ollama
try:
    import ollama
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False

# Try to import Transformers
try:
    from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False

# Try to import ONNX Runtime
try:
    import onnxruntime as ort
    ONNX_AVAILABLE = True
except ImportError:
    ONNX_AVAILABLE = False


class ModelManager:
    """Manages multiple LLM models for different tasks"""
    
    def __init__(self):
        self.settings = get_settings()
        self.loaded_models: Dict[str, Any] = {}
        self.model_configs: Dict[str, Dict] = {}
        self.model_status: Dict[str, Dict] = {}  # Track model status
        self._load_model_configs()
        
        # Get memory management settings
        mgmt_config = self.settings.get("model_management", {})
        self.lazy_loading = mgmt_config.get("lazy_loading", True)
        self.max_concurrent_models = mgmt_config.get("max_concurrent_models", 3)
        self.memory_limit_mb = mgmt_config.get("memory_limit_mb", 8192)
    
    def _load_model_configs(self):
        """Load model configurations from settings"""
        llm_models = self.settings.get("llm_models", {})
        
        # Default model configurations
        default_models = {
            "style_analysis": {
                "provider": "ollama",
                "model": "llama3.2:1b",
                "format": "gguf",
                "size": "small",
                "endpoint": os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
            },
            "text_generation": {
                "provider": "ollama",
                "model": "mistral:7b",
                "format": "gguf",
                "size": "medium",
                "endpoint": os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
            },
            "character_tracking": {
                "provider": "ollama",
                "model": "llama3.2:3b",
                "format": "gguf",
                "size": "small",
                "endpoint": os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
            },
            "plot_development": {
                "provider": "ollama",
                "model": "mistral:7b",
                "format": "gguf",
                "size": "medium",
                "endpoint": os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
            },
            "continuity_checking": {
                "provider": "ollama",
                "model": "llama3.2:1b",
                "format": "gguf",
                "size": "small",
                "endpoint": os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
            },
            "refinement": {
                "provider": "ollama",
                "model": "mistral:7b",
                "format": "gguf",
                "size": "medium",
                "endpoint": os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
            }
        }
        
        # Merge with settings
        for model_id, default_config in default_models.items():
            self.model_configs[model_id] = llm_models.get(model_id, default_config)
    
    def get_model_for_task(self, task_type: str, use_fallback: bool = True) -> Optional[Dict]:
        """
        Auto-select best model for task with fallback support
        
        Args:
            task_type: Type of task (style_analysis, text_generation, etc.)
            use_fallback: Whether to try fallback models if primary unavailable
            
        Returns:
            Model configuration dictionary
        """
        # Get task-model mapping from settings
        task_mapping = self.settings.get("model_management", {}).get("task_model_mapping", {})
        
        # Map task to model ID
        model_id = task_mapping.get(task_type, task_type)
        
        # Get primary model config
        model_config = self.model_configs.get(model_id)
        
        if not model_config:
            return None
        
        # Check if model is available
        if self._is_model_available(model_config):
            return model_config
        
        # Try fallback models if requested
        if use_fallback:
            fallback_models = model_config.get("fallback_models", [])
            for fallback_name in fallback_models:
                # Try to find fallback model config
                for config_id, config in self.model_configs.items():
                    if config.get("model") == fallback_name:
                        if self._is_model_available(config):
                            logger.info(f"Using fallback model {fallback_name} for task {task_type}")
                            return config
        
        return model_config
    
    def _is_model_available(self, model_config: Dict) -> bool:
        """Check if model is available (loaded or can be loaded)"""
        provider = model_config.get("provider", "ollama")
        model_name = model_config.get("model", "")
        
        if provider == "ollama" and OLLAMA_AVAILABLE:
            # For Ollama, check if model exists (would need to query Ollama API)
            # For now, assume available if Ollama is available
            return True
        elif provider == "transformers" and TRANSFORMERS_AVAILABLE:
            # Check if model is loaded
            cache_key = f"{provider}:{model_name}"
            return cache_key in self.loaded_models
        elif provider == "onnx" and ONNX_AVAILABLE:
            # Check if ONNX model file exists
            # This would need model path in config
            return True
        
        return False
    
    def load_model(self, model_config: Dict, lazy: bool = None) -> Optional[Any]:
        """
        Load model based on configuration
        
        Args:
            model_config: Model configuration dictionary
            lazy: Override lazy loading setting (None uses default)
            
        Returns:
            Loaded model object or None
        """
        if lazy is None:
            lazy = self.lazy_loading
        
        provider = model_config.get("provider", "ollama")
        model_name = model_config.get("model", "")
        
        if not model_name:
            logger.error("Model name not specified in config")
            return None
        
        # Check if already loaded
        cache_key = f"{provider}:{model_name}"
        if cache_key in self.loaded_models:
            self.model_status[cache_key] = {"status": "loaded", "provider": provider}
            return self.loaded_models[cache_key]
        
        # Check memory limits
        if not lazy and len(self.loaded_models) >= self.max_concurrent_models:
            logger.warning(f"Max concurrent models ({self.max_concurrent_models}) reached. Unloading least used model.")
            self._unload_least_used()
        
        try:
            if provider == "ollama" and OLLAMA_AVAILABLE:
                # Ollama models are loaded on-demand, just return config
                self.loaded_models[cache_key] = model_config
                self.model_status[cache_key] = {"status": "ready", "provider": provider}
                return model_config
            elif provider == "transformers" and TRANSFORMERS_AVAILABLE:
                # Load transformers model
                if lazy:
                    # Return config for lazy loading
                    self.model_status[cache_key] = {"status": "lazy", "provider": provider}
                    return model_config
                else:
                    model = AutoModelForCausalLM.from_pretrained(model_name)
                    tokenizer = AutoTokenizer.from_pretrained(model_name)
                    pipeline_obj = pipeline("text-generation", model=model, tokenizer=tokenizer)
                    self.loaded_models[cache_key] = pipeline_obj
                    self.model_status[cache_key] = {"status": "loaded", "provider": provider}
                    return pipeline_obj
            elif provider == "onnx" and ONNX_AVAILABLE:
                # Load ONNX model (would need model path in config)
                # For now, return config
                self.loaded_models[cache_key] = model_config
                self.model_status[cache_key] = {"status": "ready", "provider": provider}
                return model_config
            else:
                logger.error(f"Provider {provider} not available or model {model_name} not found")
                return None
        except Exception as e:
            logger.error(f"Error loading model {model_name}: {e}", exc_info=True)
            self.model_status[cache_key] = {"status": "error", "error": str(e)}
            return None
    
    def unload_model(self, model_id: str = None, cache_key: str = None):
        """
        Unload model to free memory
        
        Args:
            model_id: Model ID from config
            cache_key: Cache key (provider:model_name format)
        """
        if model_id:
            config = self.model_configs.get(model_id)
            if config:
                provider = config.get("provider", "ollama")
                model_name = config.get("model", "")
                cache_key = f"{provider}:{model_name}"
        
        if cache_key and cache_key in self.loaded_models:
            # Only unload if it's a transformers model (Ollama models don't need unloading)
            model_obj = self.loaded_models[cache_key]
            if hasattr(model_obj, 'model'):  # Transformers pipeline
                del model_obj
            del self.loaded_models[cache_key]
            if cache_key in self.model_status:
                del self.model_status[cache_key]
            logger.info(f"Unloaded model: {cache_key}")
    
    def _unload_least_used(self):
        """Unload the least recently used model"""
        # Simple implementation: unload first model (FIFO)
        if self.loaded_models:
            first_key = next(iter(self.loaded_models))
            self.unload_model(cache_key=first_key)
    
    def get_model_status(self, model_id: str = None, cache_key: str = None) -> Dict[str, Any]:
        """
        Check if model is loaded and ready
        
        Args:
            model_id: Model ID from config
            cache_key: Cache key (provider:model_name format)
            
        Returns:
            Status dictionary
        """
        if model_id:
            config = self.model_configs.get(model_id)
            if config:
                provider = config.get("provider", "ollama")
                model_name = config.get("model", "")
                cache_key = f"{provider}:{model_name}"
        
        if cache_key:
            status = self.model_status.get(cache_key, {"status": "not_loaded"})
            status["cache_key"] = cache_key
            status["is_loaded"] = cache_key in self.loaded_models
            return status
        
        return {"status": "unknown"}
    
    def get_available_models(self) -> List[Dict[str, Any]]:
        """
        List available models
        
        Returns:
            List of model information dictionaries
        """
        models = []
        
        for model_id, config in self.model_configs.items():
            models.append({
                'id': model_id,
                'name': config.get('model', ''),
                'provider': config.get('provider', ''),
                'format': config.get('format', ''),
                'size': config.get('size', ''),
                'loaded': f"{config.get('provider')}:{config.get('model')}" in self.loaded_models
            })
        
        return models
    
    def register_model(self, model_id: str, config: Dict):
        """
        Register a new model
        
        Args:
            model_id: Unique model identifier
            config: Model configuration dictionary
        """
        self.model_configs[model_id] = config
        # Save to settings
        llm_models = self.settings.get("llm_models", {})
        llm_models[model_id] = config
        self.settings.set("llm_models", llm_models)


# Global model manager instance
_model_manager: Optional[ModelManager] = None


def get_model_manager() -> ModelManager:
    """Get global model manager instance"""
    global _model_manager
    if _model_manager is None:
        _model_manager = ModelManager()
    return _model_manager

