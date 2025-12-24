import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()  # Load .env file if present

class Settings(BaseSettings):
    # GitHub
    GITHUB_TOKEN: str = os.getenv("GITHUB_TOKEN", "")
    GITHUB_REPO: str = os.getenv("GITHUB_REPO", "exo-explore/exo")
    GITHUB_API: str = "https://api.github.com"
    MAX_PRS: int = 2

    # Qdrant
    QDRANT_URL: str = os.getenv("QDRANT_URL", "http://localhost:6333")
    QDRANT_COLLECTION: str = "github_code-test"

    # OpenAI
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    LLM_MODEL: str = "gpt-4o-mini"

    # Output
    REPORTS_DIR: str = "./reports"

    # Database
    DB_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg2://github:github123@localhost:5432/github_agent"
    )

settings = Settings()
