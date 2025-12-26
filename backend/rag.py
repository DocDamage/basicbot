import chromadb
import os
from typing import List, Any
import requests
import gc
import time

class OllamaEmbeddingFunction:
    def __init__(self, base_url="http://localhost:11434", model="nomic-embed-text"):
        self.base_url = base_url
        self.model = model

    def __call__(self, input: List[str]) -> List[List[float]]:
        embeddings = []
        for text in input:
            try:
                url = f"{self.base_url}/api/embeddings"
                payload = {"model": self.model, "prompt": text}
                res = requests.post(url, json=payload)
                if res.status_code == 200:
                    embeddings.append(res.json()["embedding"])
                else:
                    embeddings.append([0.0] * 768) 
            except Exception as e:
                print(f"Embedding error: {e}")
                embeddings.append([0.0] * 768)
        return embeddings

    def name(self):
        return "ollama_embeddings"

class RAGSystem:
    def __init__(self, persist_directory="./rag_db"):
        # Force a fresh embedding function to avoid loading local ONNX models (Memory Heavy)
        self.embedding_fn = OllamaEmbeddingFunction()
        
        self.client = chromadb.PersistentClient(path=persist_directory)
        self.collection = self.client.get_or_create_collection(
            name="math_knowledge",
            embedding_function=self.embedding_fn
        )

    def query(self, query_text: str, n_results=3) -> str:
        try:
            results = self.collection.query(
                query_texts=[query_text],
                n_results=n_results
            )
            if results['documents']:
                return "\n\n".join(results['documents'][0])
        except Exception as e:
            print(f"Query Error: {e}")
        return ""

    def ingest_folder(self, folder_path: str):
        if not os.path.exists(folder_path):
            return
        
        print(f"Scanning {folder_path}...")
        
        # Collect all valid files
        all_files = []
        for root, dirs, files in os.walk(folder_path):
            for filename in files:
                if filename.endswith((".txt", ".md", ".tex", ".rst")):
                    all_files.append(os.path.join(root, filename))
        
        print(f"Found {len(all_files)} files. Ingesting via Ollama (No ONNX)...")
        
        BATCH_SIZE = 10 # Smaller batch to keep memory low
        
        current_batch_docs = []
        current_batch_ids = []
        
        for i, path in enumerate(all_files):
            try:
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                    if not content.strip() or len(content) > 500_000: # Limit 500kb
                        continue
                        
                    rel_path = os.path.relpath(path, folder_path)
                    
                    current_batch_docs.append(content)
                    current_batch_ids.append(rel_path)
                    
                    # Process batch
                    if len(current_batch_docs) >= BATCH_SIZE:
                        self.collection.upsert(
                            documents=current_batch_docs,
                            ids=current_batch_ids
                        )
                        print(f"Ingested batch ending at {rel_path}...")
                        current_batch_docs = []
                        current_batch_ids = []
                        gc.collect()
                        
            except Exception as e:
                print(f"Skipping {path}: {str(e)[:50]}")
        
        # Final batch
        if current_batch_docs:
            self.collection.upsert(documents=current_batch_docs, ids=current_batch_ids)
            gc.collect()  # Memory leak fix: collect after final batch too
        
        print(f"Ingestion complete. Processed {len(all_files)} files.")
