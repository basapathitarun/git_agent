
from llama_index.core.node_parser import CodeSplitter, SentenceSplitter
import logging

logger = logging.getLogger(__name__)

def split_code_safely(documents, language="python"):
    try:
        splitter = CodeSplitter(
            language=language,
            chunk_lines=60,
            chunk_lines_overlap=10,
            max_chars=1500,
        )
        return splitter.get_nodes_from_documents(documents)

    except Exception as e:
        logger.warning(
            f"CodeSplitter failed for language={language}, "
            f"falling back to SentenceSplitter. Error: {e}"
        )

        fallback = SentenceSplitter(
            chunk_size=800,
            chunk_overlap=120,
            separator="\n",
        )
        return fallback.get_nodes_from_documents(documents)
