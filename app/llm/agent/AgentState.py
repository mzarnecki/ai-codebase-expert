from typing import TypedDict, List, Annotated

from langgraph.graph import add_messages


# Define the state schema using TypedDict
class AgentState(TypedDict):
    ticket: str
    code: str
    messages: Annotated[list, add_messages]
    iteration_count: int  # Track iterations