import logging
import json
import os
import aiofiles
from dotenv import load_dotenv
from typing import TypedDict, Annotated, Sequence, Any, Optional
from langchain_core.messages import BaseMessage, HumanMessage, ToolMessage, AIMessage
from langgraph.graph import StateGraph, START, END
from langchain_core.tools import StructuredTool, tool
from pydantic import BaseModel, Field
from langchain_core.language_models.chat_models import BaseChatModel
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from langgraph.graph.message import add_messages

logger = logging.getLogger(__name__)

# --- GDRIVE MCP SETUP ---
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

gdrive_server_params = StdioServerParameters(
    command="node",
    args=[os.path.abspath(os.path.join(os.path.dirname(__file__), "gdrive-mcp-server", "dist", "index.js"))],
    env={
        "MCP_GDRIVE_CREDENTIALS": os.path.abspath(
            os.path.join(os.path.dirname(__file__), "gdrive-mcp-server", "credentials",
                         ".gdrive-server-credentials.json")),
        "PATH": os.environ.get("PATH", "")
    }
)


@tool
async def search_google_drive(query: str) -> str:
    """Search Google Drive for files matching a query. Returns a list of files with their names, mime types, and file_ids."""
    async with stdio_client(gdrive_server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool("gdrive_search", arguments={"query": query})
            return result.content[0].text


@tool
async def fetch_and_save_gdrive_doc(file_id: str, file_name: str) -> str:
    """Reads a document from Google Drive using its file_id and saves it locally so it can be ingested."""
    async with stdio_client(gdrive_server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool("gdrive_read_file", arguments={"file_id": file_id})
            content = result.content[0].text

            # Read DOCUMENTS_DIR from .env, fallback to relative ../docs
            docs_dir = os.environ.get("DOCUMENTS_DIR")
            if not docs_dir or not os.path.isabs(docs_dir):
                docs_dir = os.path.abspath(
                    os.path.join(os.path.dirname(__file__), '..', docs_dir.strip('./\\') if docs_dir else 'docs'))

            os.makedirs(docs_dir, exist_ok=True)

            safe_name = "".join([c for c in file_name if c.isalpha() or c.isdigit() or c == ' ']).rstrip()
            file_path = os.path.join(docs_dir, f"{safe_name}.md")

            async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
                await f.write(content)

            return f"Successfully saved to {file_path}. The file is ready for ingestion."


# --- LANGGRAPH AGENT ---
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]


class RAGAgent:
    def __init__(self, mcp_client, llm: BaseChatModel = None):
        self.mcp_client = mcp_client
        if not llm:
            from langchain_ollama import ChatOllama
            self.llm = ChatOllama(model="llama3")
        else:
            self.llm = llm
        self.tools = []
        self.graph = None

    async def initialize(self):
        mcp_tools = await self.mcp_client.get_tools()
        self.tools = []

        for t in mcp_tools:
            def create_tool_func(tool_name):
                async def invoke(*args, **kwargs):
                    logger.info(f"Invoking tool {tool_name} with {kwargs}")
                    res = await self.mcp_client.call_tool(tool_name, kwargs)
                    return str(res)

                return invoke

            properties = t.inputSchema.get("properties", {})
            required = t.inputSchema.get("required", [])
            fields = {}
            for prop_name, prop_info in properties.items():
                prop_type = Any if "type" not in prop_info else str
                if prop_name not in required:
                    fields[prop_name] = (Optional[prop_type], None)
                else:
                    fields[prop_name] = (prop_type, ...)

            from pydantic import create_model
            ToolInputModel = create_model(f"{t.name}Input", **fields)

            lc_tool = StructuredTool.from_function(
                func=create_tool_func(t.name),
                coroutine=create_tool_func(t.name),
                name=t.name,
                description=t.description,
                args_schema=ToolInputModel
            )
            self.tools.append(lc_tool)

        # ADD GDRIVE TOOLS HERE
        self.tools.extend([search_google_drive, fetch_and_save_gdrive_doc])

        # Bind tools to LLM
        if self.tools:
            self.llm_with_tools = self.llm.bind_tools(self.tools)
        else:
            self.llm_with_tools = self.llm

        workflow = StateGraph(AgentState)
        workflow.add_node("agent", self._agent_node)
        workflow.add_node("action", self._action_node)

        workflow.add_edge(START, "agent")
        workflow.add_conditional_edges("agent", self._should_continue)
        workflow.add_edge("action", "agent")
        self.graph = workflow.compile()

    async def _agent_node(self, state: AgentState):
        messages = state["messages"]
        response = await self.llm_with_tools.ainvoke(messages)
        return {"messages": [response]}

    def _should_continue(self, state: AgentState) -> str:
        messages = state["messages"]
        last_message = messages[-1]
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "action"
        return END

    async def _action_node(self, state: AgentState):
        messages = state["messages"]
        last_message = messages[-1]

        tool_responses = []
        for tool_call in last_message.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]

            tool = next((t for t in self.tools if t.name == tool_name), None)
            if tool:
                result = await tool.coroutine(**tool_args)
                tool_responses.append(
                    ToolMessage(content=str(result), tool_call_id=tool_call["id"], name=tool_name)
                )
            else:
                tool_responses.append(
                    ToolMessage(content=f"Tool {tool_name} not found", tool_call_id=tool_call["id"], name=tool_name)
                )
        return {"messages": tool_responses}

    async def ask(self, query: str) -> str:
        if not self.graph:
            raise RuntimeError("Agent not initialized")
        messages = [HumanMessage(content=query)]
        result = await self.graph.ainvoke({"messages": messages})
        return result["messages"][-1].content