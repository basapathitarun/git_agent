import requests
import base64
from typing import Optional, Dict

from config import settings



# ========================
# HELPERS
# ========================
def github_headers(token: Optional[str]):
    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def fetch_pull_requests(repo: str, token: Optional[str]):
    url = f"{settings.GITHUB_API}/repos/{repo}/pulls"
    r = requests.get(url, headers=github_headers(token))
    r.raise_for_status()
    return r.json()


def fetch_pr_files(repo: str, pr_number: int, token: Optional[str]):
    url = f"{settings.GITHUB_API}/repos/{repo}/pulls/{pr_number}/files"
    r = requests.get(url, headers=github_headers(token))
    r.raise_for_status()
    return r.json()


def fetch_raw_file(raw_url: str, token: Optional[str]):
    r = requests.get(raw_url, headers=github_headers(token))
    r.raise_for_status()
    return r.text





def get_repo_tree(owner: str, repo: str, token: Optional[str], branch="main"):
    url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/{branch}?recursive=1"

    r = requests.get(url, headers=github_headers(token))
    r.raise_for_status()
    return r.json()["tree"]


def fetch_file(owner: str, repo: str, path: str, token: Optional[str]):
    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"

    r = requests.get(url, headers=github_headers(token))
    r.raise_for_status()

    content = r.json()["content"]
    return base64.b64decode(content).decode("utf-8", errors="ignore")

