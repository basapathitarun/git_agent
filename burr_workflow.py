from burr.core import action, State, ApplicationBuilder

from config import settings
from database import get_session, PRMetadata, PRReport
from vector_store import VectorStore
from llm_client import generate_json
from report_generator import ReportGenerator

from burr.core import action, State, ApplicationBuilder


# -------------------------------------------------
# 1️⃣ Fetch PR metadata (Correct)
# -------------------------------------------------
@action(reads=[], writes=["prs"])
def fetch_pr_metadata(state: State) -> State:
    print("Fetching PR metadata from database...")
    db = get_session()
    prs = db.query(PRMetadata).all() 
    db.close()

    pr_dicts = []
    for pr in prs:
        # Calculate header stats
        total_added = sum(f.get("additions", 0) for f in pr.files)
        total_removed = sum(f.get("deletions", 0) for f in pr.files)

        pr_dicts.append({
            "pr_id": pr.id,
            "pr_number": pr.pr_number,
            "title": pr.title,
            "author": pr.author,
            "url": pr.url,
            "stats": f"+{total_added} / -{total_removed}", 
            "rich_files": pr.files # Contains patch, status, etc.
        })

    return state.update(prs=pr_dicts)


# -------------------------------------------------
# 2️⃣ Collect related context (Optimized: Reads directly from 'prs')
# -------------------------------------------------
@action(reads=["prs"], writes=["context"])
def collect_related_context(state: State) -> State:
    print("Collecting related context from vector store...")
    vector_store = VectorStore()
    context = []

    for pr in state["prs"]:
        # Extract filenames from the rich_files we fetched in Step 1
        filenames = [f["filename"] for f in pr["rich_files"]]
        
        # Search 1: File Purpose
        file_query = f"Explain the high-level purpose of these files: {filenames}"
        file_nodes = vector_store.semantic_search(file_query, k=3)

        # Search 2: Impact/Dependencies
        impact_query = f"Find code that imports or calls functions from: {filenames}"
        impact_nodes = vector_store.semantic_search(impact_query, k=3)

        context.append({
            "pr_id": pr["pr_id"],
            "file_context": [n.text for n in file_nodes],
            "impact_context": [n.text for n in impact_nodes]
        })

    return state.update(context=context)


# -------------------------------------------------
# 3️⃣ Summarize changes (Correct)
# -------------------------------------------------
@action(reads=["prs", "context"], writes=["summaries"])
def summarize_changes(state: State) -> State:
    print("Summarizing PR changes using LLM...")
    summaries = []

    for pr in state["prs"]:
        # Find matching context
        ctx = next(c for c in state["context"] if c["pr_id"] == pr["pr_id"])
        
        diff_text = ""
        # Safety check: ensure rich_files exists
        files = pr.get("rich_files", [])
        
        for f in files[:3]: 
            patch = f.get("patch", "")
            if patch:
                diff_text += f"\nFile: {f['filename']}\n{patch}\n"

        prompt = f"""
        You are generating a PR report.
        
        METADATA:
        Title: {pr['title']}
        Files Changed: {[f['filename'] for f in files]}
        
        CONTEXT:
        File Purposes: {ctx['file_context']}
        Impact Analysis: {ctx['impact_context']}
        
        CODE DIFFS:
        {diff_text[:6000]} 

        TASK:
        Return valid JSON with keys: "tldr" (list), "file_summaries" (list), "impact" (string), "key_snippet" (string code block content).
        """

        # Ensure your client parses JSON string to dict
        summary_json = generate_json(prompt)

        summaries.append({
            "pr_id": pr["pr_id"],
            "content": summary_json 
        })

    return state.update(summaries=summaries)


# -------------------------------------------------
# 4️⃣ Generate Markdown report (Corrected)
# -------------------------------------------------
@action(reads=["prs", "summaries"], writes=["reports"])
def generate_markdown_report(state: State) -> State:
    print("Generating markdown reports...")
    
    # Initialize the generator (This handles formatting & disk saving)
    generator = ReportGenerator(output_dir=settings.REPORTS_DIR)
    
    reports = []
    
    for pr in state["prs"]:
        # 1. Get the LLM data for this PR
        summary_entry = next(s for s in state["summaries"] if s["pr_id"] == pr["pr_id"])
        llm_data = summary_entry["content"]
        
        # 2. Generate the Markdown String
        md_content = generator.format_markdown(pr, llm_data)

        # 3. Save to Disk (returns the file path)
        file_path = generator.save_file(pr["pr_number"], md_content)

        # 4. Add to state so the next step (Persist) can read it
        reports.append({
            "pr_id": pr["pr_id"], 
            "markdown": md_content,
            "file_path": file_path
        })

    return state.update(reports=reports)

# -------------------------------------------------
# 5️⃣ Persist report (Corrected)
# -------------------------------------------------
@action(reads=["reports"], writes=["persisted"])
def persist_report(state: State) -> State:
    print("Persisting reports to database...")
    db = get_session()
    
    for r in state["reports"]:
        # Create or Update the DB Record
        report_record = PRReport(
            id=f"report-{r['pr_id']}",  # Unique ID
            pr_id=r["pr_id"],
            report_md=r["markdown"],    # Save the full markdown text
            file_path=r["file_path"]    # Optional: Save where it is on disk
        )
        
        # Merge handles both Insert and Update
        db.merge(report_record)

    db.commit()
    db.close()

    return state.update(persisted=True)

# -------------------------------------------------
# Build Burr Application (Updated Transitions)
# -------------------------------------------------
def build_burr_app():
    return (
        ApplicationBuilder()
        .with_actions(
            fetch_pr_metadata,
            collect_related_context,
            summarize_changes,
            generate_markdown_report,
            persist_report,
        )
        .with_transitions(
            # Direct link from Fetch -> Context
            ("fetch_pr_metadata", "collect_related_context"),
            ("collect_related_context", "summarize_changes"),
            ("summarize_changes", "generate_markdown_report"),
            ("generate_markdown_report", "persist_report"),
        )
        .with_state(
            prs=[],
            # pr_files=[], <-- REMOVED
            context=[],
            summaries=[],
            reports=[],
            persisted=False,
        )
        .with_entrypoint("fetch_pr_metadata")
        .build()
    )