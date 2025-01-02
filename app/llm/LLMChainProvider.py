import streamlit as st
from langchain.agents.chat.base import ChatAgent
from langchain.chains.conversation.base import ConversationChain
from langchain.chains.conversational_retrieval.base import ConversationalRetrievalChain
from langchain.chains.router import MultiRetrievalQAChain
from langchain.memory import ConversationBufferMemory
from langchain.retrievers import MergerRetriever
from langchain_community.chat_models import ChatOpenAI
from langchain_community.tools import DuckDuckGoSearchResults
from langchain_core.prompts import ChatPromptTemplate

from app.db.EnumDocsCollection import EnumDocsCollection
from app.db.VectorStore import VectorStore
from app.llm.PromptTemplateProvider import PromptTemplateProvider

from langchain.agents import initialize_agent, AgentType, AgentExecutor

from app.streaming import StreamHandler


class LLMChainProvider:
    @st.spinner('Analyzing documents..')
    def getLLMPrparationChainResult(self, llm: ChatOpenAI, ticket: str):
        # Setup memory for contextual conversation
        memory = ConversationBufferMemory()

        # Setup LLM and QA chain
        llm_chain = ConversationChain(
            llm=llm,
            memory=memory,
            verbose=False
        )

        result = llm_chain.invoke(input={"input": """
            You are a chatbot tasked with solving software project issues.
            The project is a website companyhouse.de and it's written in PHP language using Yii2 framework.
            Prepare message that will be used for sematic search in database for project code, project documentation and framework documentation.
            Prepare list of information and concepts that are relevant to answering for the problem described below. Take also into consideration directory structure of the project
            """ + ticket + "\n\n" + self.getProjectDirStructure()},
        )

        return result

    def getProjectDirStructure(self):
        with open("data/baseInformation/projectDirectoryStructure.txt", "r") as f:
            dir_structure = f.readlines()
        return "\n".join(dir_structure)

    @st.spinner('Analyzing documents..')
    def getLLMConversationalChainResult(self, llm: ChatOpenAI, ticket: str)->ConversationalRetrievalChain:
        # Define retrievers
        vectordbcode = VectorStore.get_vector_store(EnumDocsCollection.COMPANYHOUSE_PROJ_CODE.value)
        retrievercode = vectordbcode.as_retriever(
            search_type='similarity',
            search_kwargs={'k':10}
        )

        vectordbprojdocs = VectorStore.get_vector_store(EnumDocsCollection.COMPANYHOUSE_PROJ_DOCS.value)
        retrieverprojdocs = vectordbprojdocs.as_retriever(
            search_type='similarity',
            search_kwargs={'k':5}
        )

        vectordbframework = VectorStore.get_vector_store(EnumDocsCollection.COMPANYHOUSE_PROJ_CODE.value)
        retrieverframework = vectordbframework.as_retriever(
            search_type='similarity',
            search_kwargs={'k':5}
        )

        retriever = MergerRetriever(retrievers = [retrievercode, retrieverframework, retrieverprojdocs])

        # Setup memory for contextual conversation
        memory = ConversationBufferMemory(
            memory_key='chat_history',
            input_key='question',
            output_key='answer',
            return_messages=True
        )

        system_message_prompt = PromptTemplateProvider.getPromptTemplate(ticket, self.getProjectDirStructure())
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
        st_cb = StreamHandler(st.empty())
        result = llm_chain.invoke(
            {"question": "Find solution for described issue.", "closure": "", "main": ""},
            {"callbacks": [st_cb]}
        )

        return result

    def getLLMAgent(self, llm: ChatOpenAI, ticket: str):

        tools = [DuckDuckGoSearchResults()]
        agent = ChatAgent.from_llm_and_tools(llm, tools, verbose=True)
        st_cb = StreamHandler(st.empty())
        executor = AgentExecutor.from_agent_and_tools(agent=agent, tools=tools)

        input =  """
            You are a chatbot tasked with solving software project issues.
            The project is a website companyhouse.de and it's written in PHP language.
    
            Considering above create solution for ticket described below.
            Write working code solution and add explanation and additional instructions related to using this code if needed. 
            """ + ticket + """
            
            For solution use information from project code and documentation below.
            
            """ + self.getProjectDirStructure()

        return executor.run(input= input, callbacks=[st_cb])