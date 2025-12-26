import sys
import os

# Add backend to path so imports work
sys.path.append(os.path.join(os.path.dirname(__file__), "backend"))

from rag import RAGSystem

def force_ingest():
    print("Initializing RAG System for manual ingestion...")
    rag = RAGSystem(persist_directory="backend/rag_db")
    
    data_path = "backend/rag_data"
    print(f"Ingesting data from {data_path}...")
    
    if not os.path.exists(data_path):
        print(f"Error: {data_path} does not exist.")
        return

    rag.ingest_folder(data_path)
    print("Manual ingestion complete.")

if __name__ == "__main__":
    force_ingest()
