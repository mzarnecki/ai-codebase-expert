from langchain.agents import AgentExecutor
from langchain.agents.chat.base import ChatAgent
from langchain_community.tools import DuckDuckGoSearchResults
from langchain_core.tools import create_retriever_tool
from langgraph.graph import StateGraph, END
from langchain_core.runnables import RunnableLambda
from langgraph.graph.state import CompiledStateGraph

from app.llm.PromptTemplateProvider import PromptTemplateProvider
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate

from app.llm.agent.AgentState import AgentState

MAX_ITERATIONS = 5  # Limit the loop to avoid infinite execution

class AgentSystem:
    def __init__(self, llm, prompt_template_provider: PromptTemplateProvider, retriever_factory):
        self.llm = llm
        self.workflow = StateGraph(AgentState)
        self.prompt_template_provider = prompt_template_provider
        self.retriever_factory = retriever_factory

        # Initialize tools for Researcher
        retriever_code, retriever_docs = self.retriever_factory.get_retrievers()
        self.retriever_code_tool = create_retriever_tool(
            retriever_code, name="search_project_code", description="Search project code files."
        )
        self.retriever_docs_tool = create_retriever_tool(
            retriever_docs, name="search_framework", description="Search framework documentation."
        )
        self.tools = [DuckDuckGoSearchResults(), self.retriever_code_tool, self.retriever_docs_tool]

    def _create_agent(self, role: str, template: str):
        """Creates a simple agent that responds based on LLM prompts."""
        def agent_node(state: AgentState):
            prompt = ChatPromptTemplate.from_messages([
                SystemMessage(content=template),
                HumanMessage(content=state["ticket"])
            ])
            chain = prompt | self.llm
            response = chain.invoke({})

            new_state = {
                "messages": (state["messages"] + [response])[-15:],  # Keep only last 5 messages
                "ticket": state["ticket"],
                "code": state["code"],
                "iteration_count": state["iteration_count"] + 1  # Increment iteration count
            }
            return new_state

        return RunnableLambda(agent_node, name=role)

    def _create_agent_with_tools(self, role: str, template: str):
        """Creates an agent with tool access."""
        def agent_node(state: AgentState):
            agent = ChatAgent.from_llm_and_tools(self.llm, self.tools, verbose=True)
            executor = AgentExecutor.from_agent_and_tools(
                agent=agent,
                tools=self.tools,
                handle_parsing_errors=True,
                max_execution_time=180,
                return_source_documents=True,
                early_stopping_method="generate",
                verbose=True
            )

            input_query = {
                "input": f"{template}\n\nRelated Code:\n{state['code']}",
                "closure": "",
                "main": ""
            }

            result = executor.invoke(input_query)

            new_state = {
                "messages": (state["messages"] + [result["output"]])[-5:],
                "ticket": state["ticket"],
                "code": state["code"],
                "iteration_count": state["iteration_count"] + 1
            }
            return new_state

        return RunnableLambda(agent_node, name=role)

    def build_system(self, ticket: str, proj_dir_structure: str, code: str, image_description: str) -> CompiledStateGraph:
        """Builds the multi-agent system."""

        researcher = self._create_agent_with_tools(
            "Researcher",
            self.prompt_template_provider.get_researcher_prompt_message(ticket, code, proj_dir_structure)
        )

        research_critic = self._create_agent(
            "ResearchCritic",
            self.prompt_template_provider.get_research_critic_prompt_message(ticket, code, proj_dir_structure)
        )

        solver = self._create_agent(
            "Solver",
            self.prompt_template_provider.get_solver_prompt_template_message(ticket, code, image_description)
        )

        solution_critic = self._create_agent(
            "Critic",
            self.prompt_template_provider.get_critic_prompt_message()
        )

        self.workflow.add_node("Researcher", researcher)
        self.workflow.add_node("ResearchCritic", research_critic)
        self.workflow.add_node("Solver", solver)
        self.workflow.add_node("Critic", solution_critic)

        def research_critic_decision(state: AgentState):
            last_msg = state["messages"][-1].content

            if "MISSING_CODE" in last_msg:  # If the response suggests missing details
                return "Researcher"
            return "Solver"


        self.workflow.add_conditional_edges(
            "ResearchCritic",
            research_critic_decision,
            {"Researcher": "Researcher", "Solver": "Solver"}
        )

        self.workflow.add_edge("Researcher", "ResearchCritic")

        def solver_decision(state: AgentState):
            last_msg = state["messages"][-1].content

            if "MISSING_INFORMATION" in last_msg:  # If the response suggests missing details
                return "Researcher"
            return "Critic"

        self.workflow.add_conditional_edges(
            "Solver",
            solver_decision,
            {"Researcher": "Researcher", "Critic": "Critic"}
        )

        self.workflow.add_edge("ResearchCritic", "Solver")

        def decide_next_step(state: AgentState):
            last_msg = state["messages"][-1].content

            if "APPROVED" in last_msg:
                return END  # End workflow if solution is approved

            if state["iteration_count"] >= MAX_ITERATIONS:
                return END  # Stop after max iterations

            return "Solver"

        self.workflow.add_conditional_edges(
            "Critic",
            decide_next_step,
            {"Solver": "Solver", END: END}
        )

        self.workflow.set_entry_point("Researcher")
        return self.workflow.compile(debug=True)