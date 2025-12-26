import os
import subprocess
import shutil

# Target directory
# Ensure we map to backend/rag_data regardless of where script is run
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "rag_data")
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

# List of high-quality math repositories
REPOS = [
    "https://github.com/rossant/awesome-math",  # Curated list of math resources
    "https://github.com/HechenHu/Mathematics-Notes", # Comprehensive math notes
    "https://github.com/mitmath/1806", # Linear Algebra (MIT)
    "https://github.com/ystael/chicago-ug-math-bib", # Bibliography/Notes
]

def clone_repo(url):
    repo_name = url.split("/")[-1]
    target_path = os.path.join(DATA_DIR, repo_name)
    
    if os.path.exists(target_path):
        print(f"Update: {repo_name} already exists. Pulling latest...")
        try:
            subprocess.run(["git", "-C", target_path, "pull"], check=True)
        except Exception as e:
            print(f"Failed to pull {repo_name}: {e}")
    else:
        print(f"Downloading: {repo_name}...")
        try:
            subprocess.run(["git", "clone", "--depth", "1", url, target_path], check=True)
            print(f"Successfully downloaded {repo_name}")
        except Exception as e:
            print(f"Failed to clone {repo_name}: {e}")

    # cleanup .git folder to save space/confusion
    git_dir = os.path.join(target_path, ".git")
    if os.path.exists(git_dir):
        try:
            shutil.rmtree(git_dir)
            print(f"Cleaned up .git for {repo_name}")
        except:
            pass

def main():
    print("--- Starting Math Data Fetch ---")
    
    # Check if git is installed
    if shutil.which("git") is None:
        print("Error: 'git' is not installed or not in PATH. Please install git.")
        return

    for repo in REPOS:
        clone_repo(repo)
    
    print("--- Data Fetch Complete. Ready for Ingestion ---")

if __name__ == "__main__":
    main()
