import streamlit as st
from langchain.agents.chat.base import ChatAgent
from langchain.chains.conversation.base import ConversationChain
from langchain.chains.conversational_retrieval.base import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain_community.chat_models import ChatOpenAI
from langchain_community.tools import DuckDuckGoSearchResults
from langchain_community.utilities.dataforseo_api_search import DataForSeoAPIWrapper
from langchain_core.prompts import ChatPromptTemplate
from transformers import Tool

from app.db.EnumDocsCollection import EnumDocsCollection
from app.db.VectorStore import VectorStore
from app.llm.PromptTemplateProvider import PromptTemplateProvider

from langchain.agents import initialize_agent, AgentType, AgentExecutor

from app.streaming import StreamHandler


class LLMChainProvider:
    @st.spinner('Analyzing documents..')
    def getLLMPrparationChainResult(llm: ChatOpenAI, ticket: str):
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
            Prepare message that will be used for sematic search in database for project code and project documentation.
            Prepare message based on issue description below. Say which files should be checked.
            """ + ticket},
        )

        return result

    @st.spinner('Analyzing documents..')
    def getLLMConversationalChainResult(llm: ChatOpenAI, ticket: str)->ConversationalRetrievalChain:
        vectordb = VectorStore.get_vector_store(EnumDocsCollection.COMPANYHOUSE_PROJ_CODE.value)

        # Define retriever
        retriever = vectordb.as_retriever(
            search_type='similarity',
            search_kwargs={'k':10, 'fetch_k':10}
        )

        # Setup memory for contextual conversation
        memory = ConversationBufferMemory(
            memory_key='chat_history',
            output_key='answer',
            return_messages=True
        )

        system_message_prompt = PromptTemplateProvider.getPromptTemplate(ticket)
        prompt = ChatPromptTemplate.from_messages([system_message_prompt])

        # Setup LLM and QA chain
        llm_chain = ConversationalRetrievalChain.from_llm(
            llm=llm,
            retriever=retriever,
            memory=memory,
            return_source_documents=True,
            verbose=False,
            combine_docs_chain_kwargs={"prompt": prompt}
        )
        st_cb = StreamHandler(st.empty())
        result = llm_chain.invoke(
            {"question": "Find solution for described issue."},
            {"callbacks": [st_cb]}
        )

        return result

    def getLLMAgent(llm: ChatOpenAI, ticket: str):

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
            
            """

        return executor.run(input= input, callbacks=[st_cb])