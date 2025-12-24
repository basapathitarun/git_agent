# Github Agent

A powerful AI-driven agent that analyzes GitHub Pull Requests, understands codebase context using RAG (Retrieval-Augmented Generation), and generates detailed automated reports.

## Features
- **Codebase Ingestion**: Indexes your entire repository into a Vector Database (Qdrant).
- **Intelligent Context**: Retreives semantic context for changed files to understand *why* changes matter.
- **Automated Reporting**: Generates markdown reports summarizing PRs, architectural impact, and key code snippets.
- **Burr Workflow**: Uses a transparent state machine for reliable process orchestration.

## Prerequisites
- **Docker** and **Docker Compose**
- **OpenAI API Key** (for embeddings and LLM)
- **GitHub Personal Access Token** (for fetching repo data)

## Quick Start (Docker)

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd <repo-name>
   ```

2. **Configure Environment**
   Create a `.env` file in the root directory:
   ```env
   GITHUB_TOKEN=your_github_token
   OPENAI_API_KEY=sk-your_openai_key
   # Optional overrides
   # QDRANT_URL=http://qdrant:6333
   # DATABASE_URL=postgresql+psycopg2://github:github123@db:5432/github_agent
   ```

3. **Build and Run**
   Since the application is **interactive** (it waits for user input), run it as follows:

   ```bash
   docker-compose run --service-ports app
   ```
   
   *Alternatively, to run services in background and attach:*
   ```bash
   docker-compose up -d
   docker attach github_agent_app
   ```

## Usage
When the application starts, you will be prompted with options:

1. **Ingest Codebase**: Fetches the specified repo and builds the vector index. **(Run this first!)**
2. **Store PR Metadata**: Fetches specific PRs and stores their metadata in PostgreSQL.
3. **Generate Report**: Runs the Burr workflow to analyze the PRs and generate Markdown reports.

## Local Development (Without Docker)

1. **Install Dependencies**
   ```bash
   pip install -r requirement.txt
   ```

2. **Start Infrastructure**
   You still need Qdrant and Postgres running. You can use Docker for just the infra:
   ```bash
   docker-compose up -d qdrant db
   ```

3. **Run Application**
   ```bash
   python main.py
   ```

## Project Structure
- `main.py`: Entry point and CLI.
- `burr_workflow.py`: The core state machine logic.
- `ingestion/`: Modules for fetching and indexing code.
- `reports/`: Generated markdown reports are saved here.
