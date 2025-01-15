import streamlit as st
from langchain.agents.chat.base import ChatAgent
from langchain.chains.conversation.base import ConversationChain
from langchain.chains.conversational_retrieval.base import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain.retrievers import MergerRetriever
from langchain_community.chat_models import ChatOpenAI
from langchain_community.tools import DuckDuckGoSearchResults
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import create_retriever_tool

from app.db.EnumDocsCollection import EnumDocsCollection
from app.db.VectorStore import VectorStore
from app.llm.PromptTemplateProvider import PromptTemplateProvider

from langchain.agents import AgentExecutor

from app.streaming import StreamHandler

class LLMChainProvider:

    def __init__(self):
        self.st_cb = StreamHandler(st.empty())

    @st.spinner('Analyzing documents..')
    def getLLMPreparationChainResult(self, llm: ChatOpenAI, ticket: str, code: str):
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
            TICKET:\n""" + ticket + "\n\nPROJECT DIRECTORY STRUCTURE:\n" + self.getProjectDirStructure() + "\n\nRELATED CODE:\n" + code},
            {"callbacks": [self.st_cb]}
        )

        return result

    def getProjectDirStructure(self):
        with open("data/baseInformation/projectDirectoryStructure.txt", "r") as f:
            dir_structure = f.readlines()
        return "\n".join(dir_structure)

    @st.spinner('Analyzing documents..')
    def getLLMConversationalChainResult(self, llm: ChatOpenAI, ticket: str, code: str)->ConversationalRetrievalChain:
        retrievercode, retrieverframework, retrieverprojdocs, retrieverbaseinfo = self._getRetrievers()
        retriever = MergerRetriever(retrievers = [retrievercode, retrieverframework, retrieverprojdocs, retrieverbaseinfo])

        # Setup memory for contextual conversation
        memory = ConversationBufferMemory(
            memory_key='chat_history',
            input_key='question',
            output_key='answer',
            return_messages=True
        )

        system_message_prompt = PromptTemplateProvider.getPromptTemplate(ticket, code)
        prompt = ChatPromptTemplate.from_messages([system_message_prompt])

        # Setup LLM and QA chain
        llm_chain = ConversationalRetrievalChain.from_llm(
            llm=llm,
            retriever=retriever,
            memory=memory,
            return_source_documents=True,
            verbose=True,
            combine_docs_chain_kwargs={"prompt": prompt}
        )
        result = llm_chain.invoke(
            {"question": "Find solution for described issue.", "closure": "", "main": ""},
            {"callbacks": [self.st_cb]}
        )

        return result

    def getLLMAgent(self, llm: ChatOpenAI, ticket: str, code: str):
        retrievercode, retrieverframework, retrieverprojdocs, retrieverbaseinfo = self._getRetrievers()
        retriever_code_tool = create_retriever_tool(
            retrievercode,
            name="search_project_code",
            description="Searches and returns code files content from project.",
        )

        retriever_framework_tool = create_retriever_tool(
            retrievercode,
            name="search_framework",
            description="Searches and returns examples and information from framework documentation.",
        )

        retriever_project_documentation_tool = create_retriever_tool(
            retrievercode,
            name="search_project_documentation",
            description="Searches and returns project documentation matching pages.",
        )

        retriever_base_info_tool = create_retriever_tool(
            retrieverbaseinfo,
            name="search_base_project_information",
            description="Searches and returns project base information like dir structure and db schema.",
        )

        tools = [DuckDuckGoSearchResults(), retriever_code_tool, retriever_framework_tool,
                 retriever_project_documentation_tool, retriever_base_info_tool]
        agent = ChatAgent.from_llm_and_tools(llm, tools, verbose=True)
        executor = AgentExecutor.from_agent_and_tools(agent=agent, tools=tools, handle_parsing_errors=True)
        input = PromptTemplateProvider.getPromptTemplate(ticket, code)

        return executor.invoke(
            {"input": input, "closure": "", "main": ""},
            {"callbacks": [self.st_cb]}
        )


    def _getRetrievers(self):
        # Define retrievers
        vectordbcode = VectorStore.get_vector_store(EnumDocsCollection.COMPANYHOUSE_PROJ_CODE.value)
        retrievercode = vectordbcode.as_retriever(
            search_type='mmr',
            search_kwargs={'k':5}
        )

        vectordbprojdocs = VectorStore.get_vector_store(EnumDocsCollection.COMPANYHOUSE_PROJ_DOCS.value)
        retrieverprojdocs = vectordbprojdocs.as_retriever(
            search_type='mmr',
            search_kwargs={'k':3}
        )

        vectordbframework = VectorStore.get_vector_store(EnumDocsCollection.COMPANYHOUSE_PROJ_CODE.value)
        retrieverframework = vectordbframework.as_retriever(
            search_type='mmr',
            search_kwargs={'k':3}
        )

        vectordbbaseinfo = VectorStore.get_vector_store(EnumDocsCollection.BASE_INFO.value)
        retrieverbaseinfo = vectordbbaseinfo.as_retriever(
            search_type='mmr',
            search_kwargs={'k':3}
        )

        return retrievercode, retrieverprojdocs, retrieverframework, retrieverbaseinfo