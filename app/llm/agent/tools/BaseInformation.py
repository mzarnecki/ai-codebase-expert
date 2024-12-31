from langchain.tools import BaseTool
from typing import Optional
from langchain.callbacks.manager import AsyncCallbackManagerForToolRun, CallbackManagerForToolRun
class BaseInformation(BaseTool):
    name = "Base information about companyhouse.de project"
    description = "provide initial information about companyhouse.de project"

    def _run(self, query: str, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        # return framework documentation needed
        return ""

    async def _arun(self, query: str, run_manager: Optional[AsyncCallbackManagerForToolRun] = None) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError("not suppored")