from qdrant_client import QdrantClient
from llama_index.vector_stores.qdrant import QdrantVectorStore
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.core import VectorStoreIndex, StorageContext, Document
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.retrievers import VectorIndexRetriever
from config import settings
from llama_index.core.vector_stores import MetadataFilters, ExactMatchFilter
from qdrant_client.models import PointStruct, VectorParams,Distance


class VectorStore:
    def __init__(self):
        self.client = QdrantClient(url=settings.QDRANT_URL)
        self.vector_store = QdrantVectorStore(
            client=self.client,
            collection_name=settings.QDRANT_COLLECTION,
        )
        self.storage = StorageContext.from_defaults(vector_store=self.vector_store)
        self.embed = OpenAIEmbedding(
            api_key=settings.OPENAI_API_KEY,
            model=settings.EMBEDDING_MODEL,
        )
        self.splitter = SentenceSplitter(chunk_size=1200, chunk_overlap=200)

    def index_documents(self, docs: list[Document]):
        VectorStoreIndex.from_documents(
            docs,
            storage_context=self.storage,
            embed_model=self.embed,
            node_parser=self.splitter,
        )


    def semantic_search(
        self,
        query: str,
        file_path: str | None = None,
        k: int = 6,
    ):
        """
        Semantic vector search with optional metadata filtering.
        No LLM involved.
        """

        index = VectorStoreIndex.from_vector_store(
            self.vector_store,
            embed_model=self.embed,
        )

        filters = None
        if file_path:
            filters = MetadataFilters(
                filters=[
                    ExactMatchFilter(
                        key="file_path",
                        value=file_path,
                    )
                ]
            )

        retriever = VectorIndexRetriever(
            index=index,
            similarity_top_k=k,
            filters=filters,  
        )

        nodes = retriever.retrieve(query)
        return nodes

# def get_vector_store(collection_name: str, batch_size: int):
#     client = QdrantClient(url=settings.QDRANT_URL)

#     # ✅ ENSURE COLLECTION EXISTS
#     if not client.collection_exists(collection_name):
#         client.create_collection(
#             collection_name=collection_name,
#             vectors_config=VectorParams(
#                 size=settings.EMBEDDING_DIMENSION,  # REQUIRED
#                 distance=Distance.COSINE,
#             ),
#         )

#     return QdrantVectorStore(
#         client=client,
#         collection_name=collection_name,
#         batch_size=batch_size,
#     )