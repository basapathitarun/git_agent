from burr_workflow import build_burr_app
from database import PRMetadata,get_session
from typing import Optional
from ingestion.github_api import fetch_pull_requests, fetch_pr_files,fetch_raw_file
from ingestion.ingestion import run_ingestion
from config import settings


def ingest_prs(
    github_repo: str,
    github_token: Optional[str] = None,
    db = None
):
    """
    Ingest PRs including metadata, diffs, and file stats.
    """
    prs = fetch_pull_requests(github_repo, github_token)
    stored = []
    
    for pr in prs:
        pr_number = pr["number"]
        
        # 1. Fetch the list of files for this PR
        files = fetch_pr_files(github_repo, pr_number, github_token)
        pr_files_data = []

        for f in files:
            # 2. Skip deleted files or weird binary files if you want to save space
            if f["status"] == "removed":
                continue

            # 3. (Optional) Fetch full content if you need context the Vector DB doesn't have
            content = None
            if f.get("raw_url"):
                try:
                    content = fetch_raw_file(f["raw_url"], github_token)
                except Exception as e:
                    print(f"Warning: Could not fetch content for {f['filename']}: {e}")
            
            # 4. BUILD THE RICH OBJECT (This is the most important change)
            # You must store the 'patch' to generate snippets later.
            file_entry = {
                "filename": f["filename"],
                "status": f["status"],        # e.g., "modified", "added"
                "additions": f["additions"],  # For the "+X" stat
                "deletions": f["deletions"],  # For the "-Y" stat
                "patch": f.get("patch"),      # ✅ CRITICAL: The raw Diff text
                "content": content            # ✅ FULL CONTEXT (Optional but good)
            }
            pr_files_data.append(file_entry)

        # 5. Create the DB Record
        # Ensure your 'files' column in the DB is JSON/JSONB type!
        pr_row = PRMetadata(
            pr_number=pr_number,
            url=pr["html_url"],
            title=pr["title"],
            author=pr["user"]["login"],
            created_at=pr["created_at"],
            # Store the list of dictionaries, not just strings
            files=pr_files_data,  
            repo=github_repo
        )

        # Upsert logic (check if exists first to avoid duplicates)
        existing = db.query(PRMetadata).filter_by(pr_number=pr_number, repo=github_repo).first()
        if not existing:
            db.add(pr_row)
            stored.append(pr_number)
        else:
            # Update existing record if needed
            existing.files = pr_files_data
            
        db.commit()

    return {
        "status": "success", 
        "repo": github_repo, 
        "prs_ingested": stored
    }


if __name__ == "__main__":

    while True:
        print("\nSelect an option:")
        print("0. First-time init DB tables")
        print("1. Ingest codebase")
        print("2. Store PR metadata")
        print("3. Generate report")
        print("4. Exit")

        try:
            choice = int(input("Enter your choice: "))
        except ValueError:
            print("❌ Please enter a valid number")
            continue

        if choice == 0:
            from database import init_db
            init_db()
            print("✅ Database initialized")

        elif choice == 1:
            run_ingestion(
                owner="exo-explore",
                repo="exo",
                branch="main",
                token=settings.GITHUB_TOKEN  # ✅ secure
            )
            print("✅ Codebase ingestion completed")

        elif choice == 2:
            db_session = get_session()
            try:
                result = ingest_prs(
                    github_repo="exo-explore/exo",
                    github_token=settings.GITHUB_TOKEN,
                    db=db_session
                )
                print(f"✅ PR ingestion complete -> {result}")
            except Exception as e:
                print(f"❌ Error during PR ingestion: {e}")
            finally:
                db_session.close()

        elif choice == 3:
            print("🚀 Starting Burr App...")
            app = build_burr_app()
            app.run(halt_after=["persist_report"])

        elif choice == 4:
            print("👋 Exiting program")
            break

        else:
            print("❌ Invalid choice, please select 0–4")
