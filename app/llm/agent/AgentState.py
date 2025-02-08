from typing import TypedDict, List
from langchain_core.messages import BaseMessage

# Define the state schema using TypedDict
class AgentState(TypedDict):
    ticket: str
    code: str
    messages: List[BaseMessage]
    iteration_count: int  # Track iterations