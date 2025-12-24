from typing import List, Dict, Any, Optional
from llama_index.core import Document
from ingestion.github_api import fetch_file

SUPPORTED_EXTS = {
    ".py": "python",
    ".js": "javascript",
    ".ts": "typescript",
    ".java": "java",
    ".go": "go",
}

def build_documents(owner: str, repo: str, tree: List[Dict[str, Any]], token: Optional[str]):
    documents = []

    for item in tree:
        if item["type"] != "blob":
            continue

        for ext, lang in SUPPORTED_EXTS.items():
            if item["path"].endswith(ext):
                code = fetch_file(owner, repo, item["path"], token)

                documents.append(
                    Document(
                        text=code,
                        metadata={
                            "repo": f"{owner}/{repo}",
                            "file_path": item["path"],
                            "language": lang,
                        },
                    )
                )
                break

    return documents
