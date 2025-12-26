import gutenbergpy.textget
from gutenbergpy.gutenbergcache import GutenbergCache
import re
import os
from concurrent.futures import ThreadPoolExecutor

# Define some massive classics and interesting reads
DATASET = {
    "The-Divine-Comedy-Dante": 8800,
    "The-Prince-Machiavelli": 1232,
    "Art-Of-War-Sun-Tzu": 132,
    "Beyond-Good-and-Evil-Nietzsche": 4363,
    "The-Odyssey-Homer": 1727,
    "Calculus-Made-Easy-Thompson": 33283,
    "Relativity-Einstein": 5001,
    "Origin-of-Species-Darwin": 1228,
    "Frankenstein-Shelley": 84,
    "Dracula-Stoker": 345,
    "Metamorphosis-Kafka": 5200,
    "The-Time-Machine-Wells": 35,
    "War-and-Peace-Tolstoy": 2600,
    "Moby-Dick-Melville": 2701,
    "Great-Expectations-Dickens": 1400,
    "Pride-and-Prejudice-Austen": 1342,
    "Adventures-of-Sherlock-Holmes": 1661,
    "Alice-in-Wonderland": 11,
    "The-Yellow-Wallpaper": 1952,
    "Grimms-Fairy-Tales": 2591,
    "Beowulf": 16328,
    "The-Iliad": 6130,
    "Don-Quixote": 996,
    "Les-Miserables": 135,
    "Count-of-Monte-Cristo": 1184,
    "Phantom-of-the-Opera": 175,
    "Dr-Jekyll-and-Mr-Hyde": 43,
    "Picture-of-Dorian-Gray": 174,
    "Tale-of-Two-Cities": 98,
    "Crime-and-Punishment": 2554,
    "Brothers-Karamazov": 28054
}

def clean_and_convert_to_markdown(text, title):
    # Remove Gutenberg headers/footers (approximate)
    start_match = re.search(r"\*\*\* START OF (THE|THIS) PROJECT GUTENBERG EBOOK", text, re.IGNORECASE)
    end_match = re.search(r"\*\*\* END OF (THE|THIS) PROJECT GUTENBERG EBOOK", text, re.IGNORECASE)
    
    if start_match:
        text = text[start_match.end():]
    if end_match:
        text = text[:end_match.start()]
        
    lines = text.split('\n')
    markdown_lines = [f"# {title.replace('-', ' ')}\n"]
    
    for line in lines:
        line = line.strip()
        if not line:
            markdown_lines.append("")
            continue
            
        # Detect chapters (basic heuristic)
        if re.match(r'^(CHAPTER|BOOK|PART|SECTION)\s+[IVXLC0-9]+', line, re.IGNORECASE):
            markdown_lines.append(f"## {line}")
        else:
            markdown_lines.append(line)
            
    return "\n".join(markdown_lines)

def process_book(item):
    name, book_id = item
    try:
        print(f"Fetching {name} (ID: {book_id})...")
        # clean_extracted=True removes the main Gutenberg boilerplate automatically
        text = gutenbergpy.textget.get_text_by_id(book_id)
        if not text:
            print(f"Failed to download {name}")
            return
            
        decoded_text = text.decode('utf-8', errors='ignore')
        md_content = clean_and_convert_to_markdown(decoded_text, name)
        
        # Save to RAG data
        path = f"backend/rag_data/classics/{name}.md"
        os.makedirs(os.path.dirname(path), exist_ok=True)
        
        with open(path, "w", encoding="utf-8") as f:
            f.write(md_content)
        print(f"Saved {name} to {path}")
    except Exception as e:
        print(f"Error processing {name}: {e}")

if __name__ == "__main__":
    print("Starting Gutenberg E-Book Fetcher...")
    
    # We don't necessarily need the cache for direct ID downloads
    # GutenbergCache.create() 
    
    with ThreadPoolExecutor(max_workers=5) as executor:
        executor.map(process_book, DATASET.items())
        
    print("All books processed.")
