from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.embeddings import Embeddings

from src.rag.config import settings


class ModelFactory:
    """
    Factory class for instantiating LLMs and Embeddings based on the execution mode.
    """

    @staticmethod
    def get_llm() -> BaseChatModel:
        """
        Returns the appropriate ChatModel.
        - offline: Ollama Chat Model
        - online: Google Gemini Chat Model
        """
        if settings.execution_mode == 'offline':

            from langchain_ollama import ChatOllama
            return ChatOllama(
                model=settings.offline_llm_model,
                base_url=settings.ollama_base_url,
                temperature=0.0
            )  # type: ignore
        else:
            from langchain_google_genai import ChatGoogleGenerativeAI
            return ChatGoogleGenerativeAI(
                model="gemini-1.5-flash",
                google_api_key=settings.google_api_key,  # type: ignore
                temperature=0.0
            )

    @staticmethod
    def get_embeddings() -> Embeddings:
        """
        Returns the appropriate Embeddings model.
        - offline: HuggingFace Embeddings
        - online: Google GenAI Embeddings
        """
        if settings.execution_mode == 'offline':
            from langchain_huggingface import HuggingFaceEmbeddings
            import torch
            device = "cuda" if torch.cuda.is_available() else "cpu"
            return HuggingFaceEmbeddings(
                model_name=settings.offline_embedding_model,
                model_kwargs={"device": device}
            )
        else:
            from langchain_google_genai import GoogleGenerativeAIEmbeddings
            return GoogleGenerativeAIEmbeddings(
                model="models/text-embedding-004",
                google_api_key=settings.google_api_key  # type: ignore
            )
