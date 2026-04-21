# RAG FastMCP Integration

This project contains the integration layers (FastAPI Backend + React Vite Frontend) for the existing FastMCP RAG server.

## Architecture
1. **FastMCP Server**: The core knowledge orchestrator (`main.py`). Provides tools over MCP.
2. **FastAPI Backend**: LangGraph AI agent that acts as an MCP client. Connects to `main.py` via standard stdio on startup.
3. **React Frontend**: A Vite/TypeScript web application offering an elegant UI for interacting with the backend.

## Prerequisites
- Python 3.10+
- Node.js & npm

## Setup & Run Instructions

You will need two terminal windows to run the system concurrently.

### Terminal 1: Setup & Run Backend
The backend application automatically spawns and manages the `main.py` FastMCP server via the stdio transport protocol.

```bash
# 1. Activate your python virtual environment
# (The one where you installed the original RAG server dependencies)

# 2. Install backend client requirements
pip install -r backend/requirements.txt

# 3. Provide LLM API Keys if you want to use Gemini (optional, defaults to local ollama)
# export GOOGLE_API_KEY="your_api_key_here"

# 4. Start the FastAPI server (Run from the root of the project!)
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Terminal 2: Setup & Run Frontend

```bash
# 1. Navigate to the frontend directory
cd frontend

# 2. Install Javascript dependencies (only needed once)
npm install

# 3. Start the Vite React development server
npm run dev
```

### Usage
- Open your browser to `http://localhost:5173`.
- Use the sidebar to enter a local directory (e.g. `../docs`) and click "Sync Directory" to ingest your documents into the local ChromaDB.
- Use the chat area to talk to your documents seamlessly via the LangGraph AI!
