import asyncio
import logging
from typing import Any, Callable, Dict, List, Optional
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

logger = logging.getLogger(__name__)


class RAGServerClient:
    def __init__(self, command: str = "python", script_path: str = "../main.py"):
        self.command = command
        self.script_path = script_path
        self._session: Optional[ClientSession] = None
        self._exit_stack = None

    async def connect(self):
        from contextlib import AsyncExitStack
        self._exit_stack = AsyncExitStack()

        server_params = StdioServerParameters(
            command=self.command,
            args=[self.script_path],
            env=None
        )

        try:
            stdio_transport = await self._exit_stack.enter_async_context(stdio_client(server_params))
            read, write = stdio_transport
            self._session = await self._exit_stack.enter_async_context(ClientSession(read, write))
            await self._session.initialize()
            logger.info("Connected to FastMCP Server.")
        except Exception as e:
            logger.error(f"Failed to connect to FastMCP: {e}")
            await self.disconnect()
            raise

    async def disconnect(self):
        if self._exit_stack:
            await self._exit_stack.aclose()
            self._exit_stack = None
        self._session = None

    async def get_tools(self) -> List[Any]:
        if not self._session:
            raise RuntimeError("Not connected")
        tools_resp = await self._session.list_tools()
        return tools_resp.tools

    async def call_tool(self, name: str, arguments: dict) -> Any:
        if not self._session:
            raise RuntimeError("Not connected")
        result = await self._session.call_tool(name, arguments)
        # Extract TextContent text
        if result and hasattr(result, "content") and len(result.content) > 0:
            if hasattr(result.content[0], "text"):
                return result.content[0].text
            return str(result.content)
        return ""
