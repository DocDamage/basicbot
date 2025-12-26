"""
Centralized configuration for the Axiom Chatbot project.
All paths should be relative to PROJECT_ROOT for portability.
"""
import os

# Project root is one level up from backend/
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Backend paths
BACKEND_DIR = os.path.join(PROJECT_ROOT, "backend")
RAG_DATA_PATH = os.path.join(BACKEND_DIR, "rag_data")
RAG_DB_PATH = os.path.join(BACKEND_DIR, "rag_db")
LIBRARY_DB_PATH = os.path.join(BACKEND_DIR, "library.db")

# Library paths
LIBRARY_ROOT = os.path.join(PROJECT_ROOT, "library", "books")

# Frontend paths
FRONTEND_DIR = os.path.join(PROJECT_ROOT, "frontend")
COVERS_DIR = os.path.join(FRONTEND_DIR, "public", "covers")

# Ollama configuration
OLLAMA_BASE_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "nomic-embed-text")

# Default models
DEFAULT_MATH_MODELS = ["phi3", "qwen2:1.5b"]
DEFAULT_CONV_MODELS = ["gemma2:2b", "phi3"]
