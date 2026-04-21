import logging
import json
from typing import TypedDict, Annotated, Sequence, Any, Optional
from langchain_core.messages import BaseMessage, HumanMessage, ToolMessage, AIMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

# For simplicity, we'll try to load a default fallback model if none configured
import os
from langchain_core.language_models.chat_models import BaseChatModel

logger = logging.getLogger(__name__)

class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]

class RAGAgent:
    def __init__(self, mcp_client, llm: BaseChatModel = None):
        self.mcp_client = mcp_client
        
        if not llm:
            # Fallback to local Ollama if no LLM provided
            from langchain_ollama import ChatOllama
            self.llm = ChatOllama(model="llama3")
        else:
            self.llm = llm
            
        self.tools = []
        self.graph = None

    async def initialize(self):
        mcp_tools = await self.mcp_client.get_tools()
        
        # Convert MCP tools to Langchain StructuredTools
        self.tools = []
        for t in mcp_tools:
            def create_tool_func(tool_name):
                async def invoke(*args, **kwargs):
                    logger.info(f"Invoking tool {tool_name} with {kwargs}")
                    res = await self.mcp_client.call_tool(tool_name, kwargs)
                    return str(res)
                return invoke

            # To do proper schema extraction we would parse t.inputSchema
            # For simplicity let's use a very generic schema for now, or build it dynamically
            properties = t.inputSchema.get("properties", {})
            required = t.inputSchema.get("required", [])
            
            # create dynamic pydantic model for schema
            fields = {}
            for prop_name, prop_info in properties.items():
                prop_type = Any if "type" not in prop_info else str # simplification
                if prop_name not in required:
                    fields[prop_name] = (Optional[prop_type], None)
                else:
                    fields[prop_name] = (prop_type, ...)
                    
            # create_model requires pydantic v2 support
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

        # Bind tools to LLM
        if self.tools:
            self.llm_with_tools = self.llm.bind_tools(self.tools)
        else:
            self.llm_with_tools = self.llm

        # Build Langgraph
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
            
            # Find tool
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
        
        final_message = result["messages"][-1]
        return final_message.content
