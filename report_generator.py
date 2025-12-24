import os
from typing import Dict, Any

class ReportGenerator:
    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def format_markdown(self, pr: Dict[str, Any], data: Dict[str, Any]) -> str:
        """
        Takes PR metadata and LLM-generated JSON content and returns a formatted Markdown string.
        """
        # 1. Format TL;DR (Simple list of strings)
        tldr_list = data.get('tldr', [])
        tldr_section = "\n".join(f"- {item}" for item in tldr_list) if tldr_list else "- No summary available."

        # 2. Format Files Changed (This fixes the "Raw Dictionary" issue)
        files_raw = data.get('file_summaries', [])
        files_lines = []
        
        for item in files_raw:
            if isinstance(item, dict):
                # If LLM returns a dictionary, extract keys elegantly
                name = item.get('file', 'Unknown file')
                desc = item.get('summary', 'No description')
                files_lines.append(f"- **{name}** — {desc}")
            elif isinstance(item, str):
                # Fallback if LLM returns simple strings
                files_lines.append(f"- {item}")
        
        files_section = "\n".join(files_lines) if files_lines else "- No file summaries available."

        # 3. Clean up the Snippet
        snippet = data.get('key_snippet', '# No snippet available')
        if isinstance(snippet, str):
            snippet = snippet.strip()

        # 4. Construct Markdown (Using standard string formatting to avoid indentation bugs)
        # We perform the layout manually to ensure 100% clean output without indentation.
        md_content = f"""# PR #{pr['pr_number']}: {pr['title']}

**Author:** {pr['author']} • **URL:** {pr['url']} • **Stats:** {pr['stats']}

## TL;DR
{tldr_section}

## Files changed (high level)
{files_section}

## Impact / Risks
{data.get('impact', 'No impact analysis provided.')}

## Key code snippets / Evidence
```python
{snippet}
```"""
        return md_content

    def save_file(self, pr_number: int, markdown_content: str) -> str:
        filename = f"PR_{pr_number}_Report.md"
        file_path = os.path.join(self.output_dir, filename)
        
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(markdown_content)
            
        print(f"  💾 Report saved to: {file_path}")
        return file_path