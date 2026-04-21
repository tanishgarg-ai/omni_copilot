from typing import Any
from langchain_core.tools import BaseTool

class TruncatedToolWrapper(BaseTool):
    tool: BaseTool
    max_length: int = 4000

    def __init__(self, tool: BaseTool, max_length: int = 4000, **kwargs: Any) -> None:
        super().__init__(
            name=tool.name,
            description=tool.description,
            tool=tool,
            max_length=max_length,
            **kwargs
        )

    def _run(self, *args: Any, **kwargs: Any) -> str:
        result = self.tool._run(*args, **kwargs)
        res_str = str(result)
        return res_str[:self.max_length] + ("..." if len(res_str) > self.max_length else "")

    async def _arun(self, *args: Any, **kwargs: Any) -> str:
        if hasattr(self.tool, "_arun") and self.tool._arun:
            result = await self.tool._arun(*args, **kwargs)
        else:
            result = self.tool._run(*args, **kwargs)
        res_str = str(result)
        return res_str[:self.max_length] + ("..." if len(res_str) > self.max_length else "")