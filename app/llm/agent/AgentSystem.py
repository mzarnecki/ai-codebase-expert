from langgraph.graph import StateGraph, END
from langchain_core.runnables import RunnableLambda
from langgraph.graph.state import CompiledStateGraph

from app.llm.PromptTemplateProvider import PromptTemplateProvider
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate

from app.llm.agent.AgentState import AgentState

MAX_ITERATIONS = 5  # Limit the loop to avoid infinite execution

class AgentSystem:
    def __init__(self, llm, prompt_template_provider: PromptTemplateProvider):
        self.llm = llm
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

            new_state = {
                "messages": state["messages"] + [response],
                "ticket": state["ticket"],
                "code": state["code"],
                "iteration_count": state["iteration_count"] + 1  # Increment iteration count
            }
            return new_state

        return RunnableLambda(agent_node, name=role)

    def build_system(self, ticket: str, proj_dir_structure: str, code: str, image_description: str) -> CompiledStateGraph:
        # analyzer = self._create_agent(
        #     "Analyzer",
        #     self.prompt_template_provider.get_prompt_RAG(ticket, proj_dir_structure)
        # )

        solver = self._create_agent(
            "Solver",
            self.prompt_template_provider.get_prompt_template_message(ticket, code, image_description)
        )

        critic = self._create_agent(
            "Critic",
            """You are a senior code reviewer. Evaluate the proposed solution..."""
        )

        # self.workflow.add_node("Analyzer", analyzer)
        self.workflow.add_node("Solver", solver)
        self.workflow.add_node("Critic", critic)

        # self.workflow.add_edge("Analyzer", "Solver")
        self.workflow.add_edge("Solver", "Critic")

        def decide_next_step(state: AgentState):
            last_msg = state["messages"][-1].content

            # **Termination Conditions**
            if "APPROVED" in last_msg:
                return END  # End workflow if solution is approved

            if state["iteration_count"] >= MAX_ITERATIONS:
                return END  # Stop after max iterations

            return "Solver"  # Otherwise, continue iterating

        self.workflow.add_conditional_edges(
            "Critic",
            decide_next_step,
            {"Solver": "Solver", END: END}
        )

        self.workflow.set_entry_point("Solver")
        return self.workflow.compile(debug=True)