#!/usr/bin/env python3
"""
Main entry point for the Enhanced RAG Chatbot on Streamlit Cloud.
This file serves as the primary entry point that Streamlit Cloud will run.
"""

import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import and run the main app
from chatbot.rag_chatbot_app import main

if __name__ == "__main__":
    # Run the main application
    main()
