import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
from dotenv import load_dotenv
import sys
from mcp_client import RAGServerClient
from agent import RAGAgent


load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


import pathlib
mcp_server_path = str(pathlib.Path(__file__).parent.parent / "main.py")
mcp_client = RAGServerClient(command=sys.executable, script_path=mcp_server_path)

# Determine which llm to use based on env, wait, we don't have to fully construct it here if we want defaults
# Let's use ChatOllama or similar based on ENV if we want.
from langchain_ollama import ChatOllama
from langchain_google_genai import ChatGoogleGenerativeAI

google_api_key = os.getenv("GOOGLE_API_KEY")
if google_api_key and google_api_key != "your_google_api_key_here":
    logger.info("Using Google Generative AI")
    # Gemini requires specific initialization
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0)
else:
    logger.info("Using local Ollama")
    llm = ChatOllama(model="llama3", temperature=0)

agent = RAGAgent(mcp_client, llm=llm)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Connecting to MCP Server via stdio...")
    await mcp_client.connect()
    await agent.initialize()
    logger.info("Agent initialized with MCP tools.")
    yield
    # Shutdown
    logger.info("Disconnecting from MCP Server...")
    await mcp_client.disconnect()


app = FastAPI(lifespan=lifespan, title="RAG Client Server")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    response: str


class IngestRequest(BaseModel):
    directory_path: str


class IngestResponse(BaseModel):
    status: str


@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    try:
        response_text = await agent.ask(request.message)
        return ChatResponse(response=response_text)
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/ingest", response_model=IngestResponse)
async def ingest_endpoint(request: IngestRequest):
    try:
        # Directly call the ingest tool from mcp_client
        result = await mcp_client.call_tool("ingest_directory", {"directory_path": request.directory_path})
        return IngestResponse(status=str(result))
    except Exception as e:
        logger.error(f"Ingest error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health():
    return {"status": "ok"}
