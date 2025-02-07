from typing import TypedDict, List
from langchain_core.messages import BaseMessage
from langgraph.graph import StateGraph, END
from langchain_core.runnables import RunnableLambda
from app.llm.PromptTemplateProvider import PromptTemplateProvider
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate

# Define the state schema using TypedDict
class AgentState(TypedDict):
    ticket: str
    code: str
    messages: List[BaseMessage]

class AgentSystem:
    def __init__(self, llm, prompt_template_provider: PromptTemplateProvider):
        self.llm = llm
        # Initialize StateGraph with the TypedDict schema
        self.workflow = StateGraph(AgentState)
        self.prompt_template_provider = prompt_template_provider

    def _create_agent(self, role: str, template: str):
        def agent_node(state: AgentState):
            prompt = ChatPromptTemplate.from_messages([
                SystemMessage(content=template),
                HumanMessage(content=state["ticket"] + "\n\nRelated Code:\n" + state["code"])
            ])
            chain = prompt | self.llm
            response = chain.invoke({})
            return {"messages": state["messages"] + [response]}
        return RunnableLambda(agent_node, name=role)

    def build_system(self, ticket, proj_dir_structure):
        # Define agents (same as before)
        analyzer = self._create_agent(
            "Analyzer",
            self.prompt_template_provider.get_prompt_RAG(ticket, proj_dir_structure)
        )

        solver = self._create_agent(
            "Solver",
            self.prompt_template_provider.get_prompt_template(ticket, '', '').prompt #TODO FILL missing
        )

        critic = self._create_agent(
            "Critic",
            """You are a senior code reviewer. Evaluate the proposed solution..."""
        )

        # Add nodes and edges (same structure as before)
        self.workflow.add_node("Analyzer", analyzer)
        self.workflow.add_node("Solver", solver)
        self.workflow.add_node("Critic", critic)

        self.workflow.add_edge("Analyzer", "Solver")
        self.workflow.add_edge("Solver", "Critic")

        def decide_next_step(state: AgentState):
            last_msg = state["messages"][-1].content
            return END if "APPROVED" in last_msg else "Solver"

        self.workflow.add_conditional_edges(
            "Critic",
            decide_next_step,
            {"Solver": "Solver", END: END}
        )

        self.workflow.set_entry_point("Analyzer")
        return self.workflow.compile()