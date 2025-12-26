import os
import subprocess
import shutil

# Target directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "rag_data")
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

# Comprehensive list of "PhD-level" and high-quality academic repositories
REPOS = {
    # --- Mathematics (Existing + New) ---
    "awesome-math": "https://github.com/rossant/awesome-math",
    "Mathematics-Notes": "https://github.com/HechenHu/Mathematics-Notes",
    "mit-1806-linear-algebra": "https://github.com/mitmath/1806",
    
    # --- Physics ---
    "awesome-physics-wbierbower": "https://github.com/wbierbower/awesome-physics",
    "Lecture-notes-physics-astronomy": "https://github.com/manjunath5496/Lecture-notes-and-papers-on-physics-and-astronomy",
    "course-notes-grad-physics": "https://github.com/maho3/course-notes", # Grad level Quantum, Stat Mech
    "Uni-Notes-Physics-Edinburgh": "https://github.com/WilloughbySeago/Uni-Notes",
    
    # --- Chemistry ---
    "awesome-python-chemistry": "https://github.com/lmmentel/awesome-python-chemistry",
    "chemistry-notes-comprehensive": "https://github.com/itsmeuttu/chemistry-notes",
    
    # --- Biology / Computational Biology ---
    "awesome-biology": "https://github.com/raivivek/awesome-biology",
    "MDnotes-bio": "https://github.com/mdozmorov/MDnotes",
    
    # --- Computer Science ---
    "papers-we-love": "https://github.com/papers-we-love/papers-we-love", # Critical papers
    "system-design-primer": "https://github.com/donnemartin/system-design-primer", # Industry standard
    "tech-interview-handbook": "https://github.com/yangshun/tech-interview-handbook", # Core algos
    
    # --- General / Engineering ---
    "free-programming-books": "https://github.com/EbookFoundation/free-programming-books",
    "developer-roadmap": "https://github.com/kamranahmedse/developer-roadmap",

    # --- History (Global & Specific) ---
    "awesome-digital-history": "https://github.com/maho3/awesome-digital-history", # General & Regional sections
    "awesome-japanese": "https://github.com/yudataguy/Awesome-Japanese", # Culture/History/Lang
    "awesome-chinese": "https://github.com/thomashirtz/awesome-chinese-learning", # Culture/History/Lang
    # Note: African/Egyptian history covered in digital-history and general academic repos
    
    # --- Politics & Civics ---
    "awesome-political-science": "https://github.com/awesomelistsio/awesome-political-science",
    "awesome-democracy": "https://github.com/shacts/awesome-democracy",
    
    # --- Law & Forensics ---
    "awesome-forensics": "https://github.com/cugu/awesome-forensics",
    "uscode": "https://github.com/timlabs/uscode", # Full US Federal Laws (Markdown)
    "open-source-legislation": "https://github.com/spartypkp/open-source-legislation", # State/Global laws context
    
    # --- Arts & Industry ---
    "study-music": "https://github.com/vpavlenko/study-music", # Music Theory
    "awesome-food": "https://github.com/jzarca01/awesome-food", # Food Industry & Science
    "awesome-cooking": "https://github.com/EanNewton/Awesome-Cooking", # Beverage/Culinary

    # --- Encyclopedic Cookbooks (Massive Collections) ---
    "recipes-collection-jeffThompson": "https://github.com/jeffThompson/Recipes", # Minimalist/Clean
    "recipes-collection-schollz": "https://github.com/schollz/recipes", # Large collection
    "github-recipes": "https://github.com/githubrecipes/recipes", # Community driven
    "open-source-cookbook": "https://github.com/share-recipes/open-source-cookbook", # Structured
    "the-cookbook-jcallaghan": "https://github.com/jcallaghan/The-Cookbook", # Text archive

    # --- New Subjects (Expansion Phase) ---
    # Movies/Film
    "awesome-film-resources": "https://github.com/adammakesfilm/creative-resources",
    "awesome-movies-list": "https://github.com/stepchowfun/awesome-it-films", # IT focused but good start

    # Video Games / Game Design
    "awesome-gamedev": "https://github.com/skywind3000/awesome-gamedev",
    "awesome-game-design": "https://github.com/Roobyx/awesome-game-design",
    "awesome-ludology": "https://github.com/Kavex/GameDev-Resources",

    # Geology / Earth Science
    "awesome-open-geoscience": "https://github.com/softwareunderground/awesome-open-geoscience",
    "python-earth-science": "https://github.com/koldunovn/python_for_geosciences",

    # Dentistry / Medical
    "awesome-healthcare-dental": "https://github.com/kakoni/awesome-healthcare", # Contains Dental section
    "dental-informatics": "https://github.com/Dental-Informatics/AwesomeReadme", 

    # Edcuation / K-12
    "awesome-education": "https://github.com/abkfenris/awesome-education",
    "awesome-k12": "https://github.com/voff12/awesome-k12-education",
    
    # Technical / DSP for DDS (Signal Processing)
    "digital-signal-processing": "https://github.com/calebmadrigal/FourierTransformDemonstration", # Basic DSP
    "awesome-electronics": "https://github.com/kitspace/awesome-electronics", # Covers DDS concepts

    # --- Literature & Fiction (Analysis/Metadata) ---
    # Stephen King
    "stephen-king-api-data": "https://github.com/hvanlear/Stephen-King-API", # Data on villains, books/shorts
    "king-text-analysis": "https://github.com/erikannotations/King_data", # Stylistic analysis data
    
    # J.R.R. Tolkien
    "digital-tolkien": "https://github.com/digitaltolkien/tolkien-search", # Digital humanities project
    "lotr-api-data": "https://github.com/gitmil/lotr-api", # Character/book data
    
    # General Literature / Classics
    "awesome-books": "https://github.com/mundimark/awesome-books", # Curated classics lists
    "classic-books-markdown": "https://github.com/mlschmitt/classic-books-markdown", # Public domain text
    "pg-corpus-analysis": "https://github.com/pgcorpus/gutenberg-analysis", # Metadata on diverse writers
    "awesome-fantasy": "https://github.com/RichardLitt/awesome-fantasy", # Genre specific
}

def clone_repo(name, url):
    target_path = os.path.join(DATA_DIR, name)
    
    if os.path.exists(target_path):
        print(f"[Update] {name} already exists. Pulling latest...")
        try:
            subprocess.run(["git", "-C", target_path, "pull"], check=False) # check=False to avoid crash on dirty state
        except Exception as e:
            print(f"[Warn] Failed to pull {name}: {e}")
    else:
        print(f"[Download] Cloning: {name}...")
        try:
            # Depth 1 for speed and space saving
            subprocess.run(["git", "clone", "--depth", "1", url, target_path], check=True)
            print(f"[Success] Downloaded {name}")
        except Exception as e:
            print(f"[Error] Failed to clone {name}: {e}")

    # cleanup .git folder
    git_dir = os.path.join(target_path, ".git")
    if os.path.exists(git_dir):
        try:
            shutil.rmtree(git_dir)
            print(f"[Clean] Removed .git for {name}")
        except:
            pass

def main():
    print(f"--- Starting Knowledge Expansion (PhD Level) ---")
    print(f"Target Directory: {DATA_DIR}")
    
    # Check git
    if shutil.which("git") is None:
        print("Error: 'git' is not installed or not in PATH.")
        return

    for name, url in REPOS.items():
        clone_repo(name, url)
    
    print("--- Knowledge Expansion Complete ---")
    print("Restart the Axiom backend to ingest the new files.")

if __name__ == "__main__":
    main()
