from langchain.tools import BaseTool
from typing import Optional
from langchain.callbacks.manager import AsyncCallbackManagerForToolRun, CallbackManagerForToolRun
class ProjectCode(BaseTool):
    name = "Project code search"
    description = "search project files for needed code"

    def _run(self, query: str, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        # return code classes and files need for solving ticket
        return ""

    async def _arun(self, query: str, run_manager: Optional[AsyncCallbackManagerForToolRun] = None) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError("not suppored")