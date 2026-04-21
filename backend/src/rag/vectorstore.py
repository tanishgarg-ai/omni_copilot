import logging
from typing import List
import hashlib

from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_core.vectorstores import VectorStoreRetriever
from langchain_chroma import Chroma

from src.rag.config import settings

logger = logging.getLogger(__name__)

class VectorStoreManager:
    """
    Manages the ChromaDB instance for storing and retrieving document vectors.
    """

    def __init__(self, embeddings: Embeddings, persist_directory: str = settings.chroma_persist_dir):
        self.embeddings = embeddings
        self.persist_directory = persist_directory
        # Initialize chroma db
        self.vectorstore = Chroma(
            embedding_function=self.embeddings,
            persist_directory=self.persist_directory,
            collection_name="rag_memory"
        )

    def _generate_chunk_ids(self, chunks: List[Document]) -> List[str]:
        """
        Generates a unique ID for each chunk based on its source, content hash, 
        and position (index/page). This prevents duplication if the same file 
        is ingested multiple times and ensures uniqueness within a batch.
        """
        ids = []
        for chunk in chunks:
            source = chunk.metadata.get('source_file', chunk.metadata.get('source', 'unknown'))
            page = chunk.metadata.get('page', '0')
            start_index = chunk.metadata.get('start_index', '0')
            
            # Combine source, page, index and content to create a unique hash
            hash_input = f"{source}-{page}-{start_index}-{chunk.page_content}"
            chunk_id = hashlib.sha256(hash_input.encode('utf-8')).hexdigest()
            ids.append(chunk_id)
        return ids

    def add_documents(self, chunks: List[Document]) -> None:
        """
        Adds documents to the VectorStore if they do not already exist.
        """
        if not chunks:
            logger.info("No chunks to add to VectorStore.")
            return

        all_ids = self._generate_chunk_ids(chunks)
        
        # Deduplicate within the current batch to prevent DuplicateIDError
        unique_chunks = []
        unique_ids = []
        seen_ids = set()
        
        for chunk, chunk_id in zip(chunks, all_ids):
            if chunk_id not in seen_ids:
                unique_chunks.append(chunk)
                unique_ids.append(chunk_id)
                seen_ids.add(chunk_id)
        
        duplicate_count = len(chunks) - len(unique_chunks)
        if duplicate_count > 0:
            logger.warning(f"Filtered out {duplicate_count} duplicate chunks from the batch.")

        total_chunks = len(unique_chunks)
        logger.info(f"Adding/Updating {total_chunks} unique chunks in VectorStore.")

        # ChromaDB has a maximum batch size for adding documents (around 5461).
        # We process documents in batches to avoid ValueError.
        batch_size = 5000
        for i in range(0, total_chunks, batch_size):
            batch_chunks = unique_chunks[i : i + batch_size]
            batch_ids = unique_ids[i : i + batch_size]
            
            logger.info(f"Adding batch {i // batch_size + 1} of {(total_chunks - 1) // batch_size + 1} ({len(batch_chunks)} chunks)...")
            self.vectorstore.add_documents(documents=batch_chunks, ids=batch_ids)

        logger.info("VectorStore updated successfully.")

    def get_retriever(self, search_type: str = "similarity", k: int = 4) -> VectorStoreRetriever:
        """
        Returns a retriever instance for querying the VectorStore.
        """
        return self.vectorstore.as_retriever(
            search_type=search_type,
            search_kwargs={"k": k}
        )

