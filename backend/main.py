import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import sys
import pathlib

from config import settings
from db.database import create_tables
from api.auth import router as auth_router
from mcp_client import RAGServerClient
from agent import RAGAgent
from agent import RAGAgent, search_google_drive, fetch_and_save_gdrive_doc

from langchain_ollama import ChatOllama
from langchain_google_genai import ChatGoogleGenerativeAI

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

mcp_server_path = str(pathlib.Path(__file__).parent.parent / "main.py")
mcp_client = RAGServerClient(command=sys.executable, script_path=mcp_server_path)

if settings.execution_mode == "online" and settings.google_api_key:
    logger.info("Using Google Generative AI")
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0)
else:
    logger.info("Using local Ollama")
    llm = ChatOllama(model=settings.offline_llm_model, temperature=0, base_url=settings.ollama_base_url)

agent = RAGAgent(llm)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Initialize DB
    logger.info("Initializing database...")
    await create_tables()

    # 2. Connect to Local MCP
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

# Mount the auth routes
app.include_router(auth_router, prefix=settings.api_v1_prefix)


# ... [Keep your existing ChatRequest, IngestRequest, chat_endpoint, ingest_endpoint, health definitions here] ...
# --- MODELS ---
class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str

class IngestRequest(BaseModel):
    directory_path: str

class IngestResponse(BaseModel):
    status: str

class GDriveSearchRequest(BaseModel):
    query: str

class GDriveFetchRequest(BaseModel):
    file_id: str
    file_name: str

# --- ENDPOINTS ---
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
        result = await mcp_client.call_tool("ingest_directory", {"directory_path": request.directory_path})
        return IngestResponse(status=str(result))
    except Exception as e:
        logger.error(f"Ingest error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/gdrive/search")
async def gdrive_search_endpoint(request: GDriveSearchRequest):
    try:
        result = await search_google_drive.ainvoke({"query": request.query})
        return {"result": result}
    except Exception as e:
        logger.error(f"GDrive search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/gdrive/fetch")
async def gdrive_fetch_endpoint(request: GDriveFetchRequest):
    try:
        result = await fetch_and_save_gdrive_doc.ainvoke({"file_id": request.file_id, "file_name": request.file_name})
        return {"status": result}
    except Exception as e:
        logger.error(f"GDrive fetch error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health():
    return {"status": "ok"}