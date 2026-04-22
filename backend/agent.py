import logging
import os
import aiofiles
from dotenv import load_dotenv
from typing import TypedDict, Annotated, Sequence

from langchain_core.messages import BaseMessage, HumanMessage, ToolMessage
from langgraph.graph import StateGraph, START, END
from langchain_core.tools import tool
from langchain_core.language_models.chat_models import BaseChatModel
from langgraph.graph.message import add_messages

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

logger = logging.getLogger(__name__)
load_dotenv()


# ---------------- STATE ----------------
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]


# ---------------- AGENT ----------------
class RAGAgent:
    def __init__(self, llm: BaseChatModel):
        self.llm = llm
        self.tools = []
        self.graph = None

    async def initialize(self):
        """Initialize tools + graph"""

        # Add MCP tools
        self.tools = [
            search_google_drive,
            fetch_and_save_gdrive_doc,
        ]

        # Bind tools to LLM
        if self.tools:
            self.llm_with_tools = self.llm.bind_tools(self.tools)
        else:
            self.llm_with_tools = self.llm

        logger.info(f"Loaded {len(self.tools)} tools")

        # --- GRAPH ---
        workflow = StateGraph(AgentState)

        workflow.add_node("agent", self._agent_node)
        workflow.add_node("action", self._action_node)

        workflow.add_edge(START, "agent")
        workflow.add_conditional_edges("agent", self._should_continue)
        workflow.add_edge("action", "agent")

        self.graph = workflow.compile()

    async def _agent_node(self, state: AgentState):
        response = await self.llm_with_tools.ainvoke(state["messages"])
        return {"messages": [response]}

    def _should_continue(self, state: AgentState) -> str:
        last_message = state["messages"][-1]
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "action"
        return END

    async def _action_node(self, state: AgentState):
        last_message = state["messages"][-1]
        tool_responses = []

        for tool_call in last_message.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]

            tool = next((t for t in self.tools if t.name == tool_name), None)

            if tool:
                try:
                    result = await tool.ainvoke(tool_args)
                except Exception as e:
                    result = f"Error: {str(e)}"

                tool_responses.append(
                    ToolMessage(
                        content=str(result),
                        tool_call_id=tool_call["id"],
                        name=tool_name,
                    )
                )
            else:
                tool_responses.append(
                    ToolMessage(
                        content=f"Tool {tool_name} not found",
                        tool_call_id=tool_call["id"],
                        name=tool_name,
                    )
                )

        return {"messages": tool_responses}

    async def ask(self, query: str) -> str:
        if not self.graph:
            raise RuntimeError("Agent not initialized")

        result = await self.graph.ainvoke({
            "messages": [HumanMessage(content=query)]
        })

        return result["messages"][-1].content


# ---------------- MCP GDRIVE ----------------
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
    """Search Google Drive for files matching the given query."""
    async with stdio_client(gdrive_server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool("gdrive_search", arguments={"query": query})
            return result.content[0].text


@tool
async def fetch_and_save_gdrive_doc(file_id: str, file_name: str) -> str:
    """Fetch a document from Google Drive by its file ID and save it locally."""
    async with stdio_client(gdrive_server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool("gdrive_read_file", arguments={"file_id": file_id})
            content = result.content[0].text

            docs_dir = os.environ.get("DOCUMENTS_DIR", "docs")
            docs_dir = os.path.abspath(docs_dir)

            os.makedirs(docs_dir, exist_ok=True)

            safe_name = "".join([c for c in file_name if c.isalnum() or c == ' ']).rstrip()
            file_path = os.path.join(docs_dir, f"{safe_name}.md")

            async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
                await f.write(content)

            return f"Saved to {file_path}"