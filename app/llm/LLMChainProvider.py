import streamlit as st
from langchain.agents.chat.base import ChatAgent
from langchain.chains.conversation.base import ConversationChain
from langchain.chains.conversational_retrieval.base import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain.retrievers import MergerRetriever
from langchain_community.chat_models import ChatOpenAI
from langchain_community.tools import DuckDuckGoSearchResults
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import create_retriever_tool

from app.db.CodeGraph import CodeGraph
from app.db.EnumDocsCollection import EnumDocsCollection
from app.db.VectorStore import VectorStore
from app.llm.PromptTemplateProvider import PromptTemplateProvider

from langchain.agents import AgentExecutor

from app.llm.agent.AgentSystem import AgentSystem
from app.streaming import StreamHandler

class LLMChainProvider:

    def __init__(self):
        self.st_cb = StreamHandler(st.empty())
        self.code_graph = CodeGraph.load('../data/graph/graph.pickle')  # Load pre-built graph

    def _enhance_documents(self, docs):
        enhanced = []
        for doc in docs:
            metadata = doc.metadata
            relations = self.code_graph.get_relations(metadata['file_path'])

            # Create enhanced metadata
            enhanced_metadata = {
                **metadata,
                'parent_file': relations['parent'],
                'dependency_files': relations['dependencies'],
                'all_related_files': relations['all_related']
            }

            # Create new document with expanded content
            enhanced_content = (
                f"File: {metadata['file_path']}\n"
                f"Parent: {relations['parent'] or 'None'}\n"
                f"Dependencies: {', '.join(relations['dependencies']) or 'None'}\n"
                f"Content:\n{doc.page_content}"
            )

            enhanced.append(Document(
                page_content=enhanced_content,
                metadata=enhanced_metadata
            ))
        return enhanced

    @st.spinner('Analyzing documents..')
    def get_llm_preparation_chain_result(self, llm: ChatOpenAI, ticket: str, code: str):
        # Setup memory for contextual conversation
        memory = ConversationBufferMemory()

        # Setup LLM and QA chain
        llm_chain = ConversationChain(
            llm=llm,
            memory=memory,
            verbose=False,
        )

        result = llm_chain.invoke({"input": """
            You are a chatbot tasked with solving software project issues.
            The project is a website companyhouse.de and it's written in PHP language using Yii2 framework.
            Prepare message that will be used for semantic search in database for project code, project documentation and framework documentation.
            Prepare list of information and concepts that are relevant to answering for the problem described below. Take also into consideration directory structure of the project
            TICKET:\n""" + ticket + "\n\nPROJECT DIRECTORY STRUCTURE:\n" + self.get_project_dir_structure() + "\n\nRELATED CODE:\n" + code},
                                  {"callbacks": [self.st_cb]}
                                  )

        return result

    def get_project_dir_structure(self):
        with open("data/baseInformation/projectDirectoryStructure.txt", "r") as f:
            dir_structure = f.readlines()
        return "\n".join(dir_structure)

    @st.spinner('Analyzing documents..')
    def get_llm_conversational_chain_result(self, llm: ChatOpenAI, ticket: str, code: str) -> ConversationalRetrievalChain:
        retriever_code, retriever_docs = self._get_retrievers()

        # Create merger retriever that combines both sources
        merged_retriever = MergerRetriever(
            retrievers=[retriever_code, retriever_docs]
        )

        memory = ConversationBufferMemory(
            memory_key='chat_history',
            input_key='question',
            output_key='answer',
            return_messages=True
        )

        system_message_prompt = PromptTemplateProvider.get_prompt_template(ticket, code)
        prompt = ChatPromptTemplate.from_messages([system_message_prompt])

        return ConversationalRetrievalChain.from_llm(
            llm=llm,
            retriever=merged_retriever,
            memory=memory,
            return_source_documents=True,
            verbose=True,
            combine_docs_chain_kwargs={"prompt": prompt}
        )

    def get_llm_agent(self, llm: ChatOpenAI, ticket: str, code: str):
        retriever_code, retriever_docs = self._get_retrievers()
        retriever_code_tool = create_retriever_tool(
            retriever_code,
            name="search_project_code",
            description="Searches and returns code files content from project.",
        )

        retriever_docs_tool = create_retriever_tool(
            retriever_docs,
            name="search_framework",
            description="Searches and returns examples and information from framework documentation.",
        )

        tools = [DuckDuckGoSearchResults(), retriever_code_tool, retriever_docs_tool]
        agent = ChatAgent.from_llm_and_tools(llm, tools, verbose=True)
        executor = AgentExecutor.from_agent_and_tools(agent=agent, tools=tools, handle_parsing_errors=True)
        input = PromptTemplateProvider.get_prompt_template(ticket, code)

        return executor.invoke(
            {"input": input, "closure": "", "main": ""},
            {"callbacks": [self.st_cb]}
        )


    def _get_retrievers(self):
        vectordbcode = VectorStore.get_vector_store(EnumDocsCollection.CODE.value)

        # Create graph-aware retriever
        base_retriever = vectordbcode.as_retriever(
            search_type='mmr',
            search_kwargs={'k': 8, "lambda_mult": 0.5}
        )

        # Wrap with graph enhancement
        graph_retriever = base_retriever | self._enhance_documents

        # Documentation retriever remains the same
        vectordbdocs = VectorStore.get_vector_store(EnumDocsCollection.DOCUMENTATION.value)
        retrieverdocs = vectordbdocs.as_retriever(
            search_type='mmr',
            search_kwargs={'k': 8, "lambda_mult": 0.5}
        )

        return graph_retriever, retrieverdocs


    def get_multi_agent_system(self, llm: ChatOpenAI, ticket: str, code: str):
        agent_system = AgentSystem(llm)
        workflow = agent_system.build_system()

        result = workflow.invoke({
            "ticket": ticket,
            "code": code,
            "messages": []
        })

        return self._process_final_response(result)

    def _process_final_response(self, workflow_output):
        final_response = next(
            msg for msg in reversed(workflow_output["messages"])
            if "APPROVED" in msg.content
        )
        return {
            "answer": final_response.content,
            "source_documents": []  # Add document tracking if needed
        }