import logging
from typing import Dict, Any, List

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.vectorstores import VectorStoreRetriever
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

logger = logging.getLogger(__name__)


class RAGQueryEngine:
    """
    RAG Engine compatible with LangChain v1.x (Runnable-based API)
    """

    def __init__(self, llm: BaseChatModel, retriever: VectorStoreRetriever):
        self.llm = llm
        self.retriever = retriever
        self.chain = self._build_chain()

    def _format_docs(self, docs: List) -> str:
        return "\n\n".join(doc.page_content for doc in docs)

    def _build_chain(self):
        system_prompt = (
            "You are an intelligent assistant designed to answer questions strictly based on the provided context. "
            "If the answer is not present in the context, say: 'I don't know based on the provided context.' "
            "Provide concise and accurate answers.\n\n"
            "Context:\n{context}"
        )

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "{input}"),
        ])

        # Runnable RAG pipeline
        rag_chain = (
            {
                "context": self.retriever | self._format_docs,
                "input": RunnablePassthrough()
            }
            | prompt
            | self.llm
            | StrOutputParser()
        )

        return rag_chain

    def query(self, question: str) -> Dict[str, Any]:
        logger.info(f"Processing query: {question}")

        answer = self.chain.invoke(question)

        return {
            "answer": answer
        }
