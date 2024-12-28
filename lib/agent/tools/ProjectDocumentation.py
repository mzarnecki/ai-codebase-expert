from langchain.tools import BaseTool
from typing import Optional
from langchain.callbacks.manager import AsyncCallbackManagerForToolRun, CallbackManagerForToolRun
class ProjectDocumentation(BaseTool):
    name = "Project documentation search"
    description = "search for information in project documentation"

    def _run(self, query: str, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        # return info from project documentation
        return ""

    async def _arun(self, query: str, run_manager: Optional[AsyncCallbackManagerForToolRun] = None) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError("not suppored")