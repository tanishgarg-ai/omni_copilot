import os
from pathlib import Path
from typing import List
import logging

from langchain_core.documents import Document
from langchain_community.document_loaders import PyPDFLoader, TextLoader, UnstructuredMarkdownLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

logger = logging.getLogger(__name__)

class DocumentIngestor:
    """
    Handles the loading and chunking of documents from a local directory.
    Supports .txt, .md, and .pdf files.
    """

    def __init__(self, directory_path: str, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.directory_path = Path(directory_path)
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            add_start_index=True
        )

    def load_documents(self) -> List[Document]:
        """
        Scans the directory for supported files, loads their content,
        and returns a list of loaded Langchain Document objects.
        """
        if not self.directory_path.exists():
            logger.warning(f"Directory {self.directory_path} does not exist. Returning empty list.")
            return []

        # List of directories to skip
        ignored_dirs = {
            "node_modules", ".git", ".venv", ".env", "__pycache__", 
            "build", "dist", ".idea", ".vscode"
        }

        documents = []
        for root, dirs, files in os.walk(self.directory_path):
            # Prune ignored directories in-place so os.walk doesn't descend into them
            dirs[:] = [d for d in dirs if d not in ignored_dirs]
            
            for file in files:
                file_path = Path(root) / file
                extension = file_path.suffix.lower()
                loader = None

                try:
                    if extension == ".txt":
                        loader = TextLoader(str(file_path), encoding='utf-8')
                    elif extension == ".md":
                        loader = TextLoader(str(file_path), encoding='utf-8')
                    elif extension == ".pdf":
                        loader = PyPDFLoader(str(file_path))
                    else:
                        continue

                    if loader:
                        loaded_docs = loader.load()
                        for doc in loaded_docs:
                            doc.metadata['source_file'] = str(file_path)
                        documents.extend(loaded_docs)
                        
                except Exception as e:
                    logger.error(f"Error loading file {file_path}: {e}")

        logger.info(f"Successfully loaded {len(documents)} raw document(s).")
        return documents

    def chunk_documents(self, documents: List[Document]) -> List[Document]:
        """
        Splits a list of documents into structural chunks.
        """
        chunks = self.text_splitter.split_documents(documents)
        logger.info(f"Split raw documents into {len(chunks)} chunk(s).")
        return chunks

    def process_directory(self) -> List[Document]:
        """
        High-level method that strings together loading and chunking.
        """
        docs = self.load_documents()
        if not docs:
            return []
        return self.chunk_documents(docs)

