from langgraph.graph import StateGraph, END
from langchain_core.runnables import RunnableLambda
from app.llm.PromptTemplateProvider import PromptTemplateProvider
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate

class AgentSystem:
    def __init__(self, llm):
        self.llm = llm
        self.workflow = StateGraph({"messages": []})

    def _create_agent(self, role: str, template: str):
        def agent_node(state):
            prompt = ChatPromptTemplate.from_messages([
                SystemMessage(content=template),
                HumanMessage(content=state["ticket"] + "\n\nRelated Code:\n" + state["code"])
            ])
            chain = prompt | self.llm
            return {"messages": [chain.invoke({})]}
        return RunnableLambda(agent_node, name=role)

    def build_system(self):
        # Define agents
        analyzer = self._create_agent(
            "Analyzer",
            PromptTemplateProvider.get_prompt_RAG("", "")
        )

        solver = self._create_agent(
            "Solver",
            PromptTemplateProvider.get_prompt_template("", "").template
        )

        critic = self._create_agent(
            "Critic",
            """You are a senior code reviewer. Evaluate the proposed solution for:
            - Technical correctness
            - Adherence to Yii2 best practices
            - Architecture alignment
            - Potential edge cases
            Return either APPROVED or REVISION_REQUEST with feedback."""
        )

        # Define workflow
        self.workflow.add_node("Analyzer", analyzer)
        self.workflow.add_node("Solver", solver)
        self.workflow.add_node("Critic", critic)

        # Define edges
        self.workflow.add_edge("Analyzer", "Solver")
        self.workflow.add_edge("Solver", "Critic")

        def decide_next_step(state):
            last_msg = state["messages"][-1].content
            if "APPROVED" in last_msg:
                return END
            return "Solver"

        self.workflow.add_conditional_edges(
            "Critic",
            decide_next_step,
            {"Solver": "Solver", END: END}
        )

        self.workflow.set_entry_point("Analyzer")
        return self.workflow.compile()