from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import os
import sys

# Add backend to path for proper imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mbad import MBADSystem, OllamaClient
from rag import RAGSystem

app = FastAPI(title="Axiom Math Chatbot")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instances
ollama_client = OllamaClient()
rag_system = RAGSystem()
# Default models - Switching to Small Language Models (SLMs)
# Math: phi3 (3.8B - excellent reasoning), qwen2:1.5b
# Conv: gemma2:2b, phi3
mbad_system = MBADSystem(ollama_client, ["phi3", "qwen2:1.5b"], ["gemma2:2b", "phi3"])

class ChatRequest(BaseModel):
    message: str
    history: List[dict] = []
    mode: str = "auto" # 'auto', 'math', 'chat'

class ConfigRequest(BaseModel):
    math_models: List[str]
    conv_models: List[str]

@app.on_event("startup")
async def startup_event():
    # Attempt to ingest initial data
    if not os.path.exists("./rag_data"):
        os.makedirs("./rag_data")
        # specific dummy file
        with open("./rag_data/intro.txt", "w") as f:
            f.write("Axiom is a specialized chatbot for advanced mathematics.")
    
    # CRITICAL: Do NOT ingest on startup heavily, it blocks the server.
    # We rely on the force_ingest.py script or the /api/ingest endpoint for updates.
    # rag_system.ingest_folder("./rag_data") 
    print("System Interface Ready. Knowledge base is persistent.")

@app.post("/api/chat")
async def chat_endpoint(req: ChatRequest):
    # Retrieve context
    context = rag_system.query(req.message)
    
    # Determine mode if auto (simple keyword check for now, or use LLM classifier)
    mode = req.mode
    if mode == "auto":
        math_keywords = ["solve", "calculate", "equation", "deriv", "integral", "math", "proof", "compute"]
        if any(k in req.message.lower() for k in math_keywords):
            mode = "math"
        else:
            mode = "chat"

    if mode == "math":
        # Tandem/MBAD execution
        result = mbad_system.process_math_query_tandem(req.message, context)
        return {
            "response": result["final_analysis"],
            "details": {
                "agent_1": result["solution_1"],
                "agent_2": result["solution_2"]
            },
            "mode": "math"
        }
    else:
        # Standard chat
        response = mbad_system.process_general_chat(req.history + [{"role": "user", "content": req.message}], context)
        return {
            "response": response,
            "mode": "chat"
        }

@app.post("/api/config")
async def update_config(req: ConfigRequest):
    global mbad_system
    mbad_system = MBADSystem(ollama_client, req.math_models, req.conv_models)
    return {"status": "updated", "config": req.dict()}

@app.post("/api/ingest")
async def ingest_documents():
    rag_system.ingest_folder("./rag_data")
    return {"status": "ingested"}

# --- Library / E-Book API ---
import sqlite3
import threading

def get_library_db():
    conn = sqlite3.connect("library.db")
    conn.row_factory = sqlite3.Row
    return conn

@app.get("/api/library")
async def get_library(page: int = 1, limit: int = 20, search: str = ""):
    conn = None
    try:
        conn = get_library_db()
        offset = (page - 1) * limit
        
        if search:
            query = "SELECT * FROM books WHERE title LIKE ? OR author LIKE ? LIMIT ? OFFSET ?"
            search_term = f"%{search}%"
            books = conn.execute(query, (search_term, search_term, limit, offset)).fetchall()
            total = conn.execute("SELECT COUNT(*) FROM books WHERE title LIKE ? OR author LIKE ?", (search_term, search_term)).fetchone()[0]
        else:
            books = conn.execute("SELECT * FROM books LIMIT ? OFFSET ?", (limit, offset)).fetchall()
            total = conn.execute("SELECT COUNT(*) FROM books").fetchone()[0]
        
        return {
            "books": [dict(b) for b in books],
            "total": total,
            "page": page,
            "pages": (total // limit) + 1
        }
    finally:
        if conn:
            conn.close()

@app.get("/api/library/{book_id}/content")
async def get_book_content(book_id: str):
    conn = None
    try:
        conn = get_library_db()
        files = conn.execute("SELECT file_path, format FROM book_files WHERE book_id = ?", (book_id,)).fetchall()
    finally:
        if conn:
            conn.close()
    
    if not files:
        raise HTTPException(status_code=404, detail="Book content not found")
    
    target_file = files[0]['file_path']
    for f in files:
        if f['format'] in ['epub', 'txt', 'md']:
            target_file = f['file_path']
            break
            
    try:
        if target_file.endswith(".txt") or target_file.endswith(".md"):
            with open(target_file, "r", encoding="utf-8", errors="ignore") as f:
                return {"content": f.read()}
        elif target_file.endswith(".epub"):
            import ebooklib
            from ebooklib import epub
            from bs4 import BeautifulSoup
            import gc
            book = epub.read_epub(target_file)
            text = []
            for item in book.get_items():
                if item.get_type() == ebooklib.ITEM_DOCUMENT:
                    soup = BeautifulSoup(item.get_body_content(), 'html.parser')
                    text.append(soup.get_text())
                    soup.decompose()  # Memory leak fix: explicitly clear BeautifulSoup tree
            content = "\n".join(text)
            del book, text  # Memory leak fix: explicitly delete large objects
            gc.collect()  # Force garbage collection
            return {"content": content}
        else:
            return {"content": "Preview not available for this format."}
    except Exception as e:
        return {"content": f"Error reading file: {str(e)}"}

@app.post("/api/library/scan")
async def scan_library_endpoint():
    from ebook_ingest import scan_library
    t = threading.Thread(target=scan_library)
    t.start()
    return {"status": "Scan initiated"}

