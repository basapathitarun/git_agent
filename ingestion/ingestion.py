# clone the repo (or fetch files via githib api)
# for each source file :
    #  compute embeddings (by chunking large files into 512 -1500 token chunks).
    #  store : file_path , chunk_id , code_snippet, embedding_vector, language, repo_commit etc.
# provide sql migrations(if using sql dbs)/ schema; store provenance (commit sha, url)

from typing import Optional
from config import settings
from ingestion.github_api import get_repo_tree
from ingestion.document import build_documents
from ingestion.splitter import split_code_safely
from vector_store import VectorStore
import requests

from llama_index.core import VectorStoreIndex,StorageContext
from llama_index.embeddings.openai import OpenAIEmbedding




def run_ingestion(owner: str, repo: str, branch: str, token: Optional[str]):
    print("🔹 Fetching repository tree...")
    tree = get_repo_tree(
        owner,
        repo,
        token,
        branch,
    )

    print("🔹 Building documents...")
    documents = build_documents(
        owner,
        repo,
        tree,
        token,
    )

    print(f"🔹 Loaded {len(documents)} files")

    nodes = split_code_safely(documents, language="python")

    print(f"🔹 Created {len(nodes)} code chunks")

    vector_client = VectorStore()
    embed_model = vector_client.embed
    vector_store = vector_client.vector_store

    print("🔹 Storing embeddings in Qdrant...")
    storage_context = StorageContext.from_defaults(vector_store=vector_store)
    index = VectorStoreIndex.from_documents(
        documents=[],
        storage_context=storage_context,
        embed_model=embed_model,
    )
    print(f"🔹 Inserting {len(nodes)} nodes into the index...")
    print(f"nodes sample: {nodes[0].get_text()}")
    index.insert_nodes(nodes)

    print("✅ Ingestion complete")


