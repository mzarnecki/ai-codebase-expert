import base64

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
from langchain_openai import OpenAI

from app.db.CodeGraph import CodeGraph
from app.llm.PromptTemplateProvider import PromptTemplateProvider

from langchain.agents import AgentExecutor

from app.llm.agent.AgentSystem import AgentSystem
from app.llm.retriever.RetrieverFactory import RetrieverFactory
from app.streaming import StreamHandler

class LLMChainProvider:

    def __init__(self):
        self.st_cb = StreamHandler(st.empty())
        self.code_graph = CodeGraph.load('data/graph/graph.pickle')  # Load pre-built graph
        self.retriever_factory = RetrieverFactory()
        self.prompt_template_provider = PromptTemplateProvider()

    @st.spinner('Analyzing documents..')
    def get_llm_preparation_chain_result(
            self,
            llm: ChatOpenAI,
            ticket: str,
            code: str,
            image_description: str
    ):
        # Setup memory for contextual conversation
        memory = ConversationBufferMemory()

        # Setup LLM and QA chain
        llm_chain = ConversationChain(
            llm=llm,
            memory=memory,
            verbose=False,
        )
        prompt_message = """
            You are a chatbot tasked with solving software project issues.
            The project is a website companyhouse.de and it's written in PHP language using Yii2 framework.
            Prepare message that will be used for semantic search in database for project code, project documentation and framework documentation.
            Prepare list of information and concepts that are relevant to answering for the problem described below. Take also into consideration directory structure of the project
            TICKET:\n""" + ticket + "\n\nPROJECT DIRECTORY STRUCTURE:\n" + self._get_project_dir_structure() + code

        if code:
            prompt_message = prompt_message + "\n\nRELATED CODE:\n" + code

        if image_description:
            prompt_message = prompt_message + "\n\nIMAGE DESCRIPTION:\n" + image_description

        prompt = {"input": prompt_message}

        result = llm_chain.invoke(prompt)

        return result

    @st.spinner('Analyzing documents..')
    def get_llm_conversational_chain_result(self, llm: ChatOpenAI, ticket: str, code: str, image_description: str):
        retriever_code, retriever_docs = self.retriever_factory.get_retrievers()

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

        system_message_prompt = self.prompt_template_provider.get_prompt_template(ticket, code, image_description)
        prompt = ChatPromptTemplate.from_messages([system_message_prompt])

        llm_chain = ConversationalRetrievalChain.from_llm(
            llm=llm,
            retriever=merged_retriever,
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

    @st.spinner('Analyzing documents..')
    def get_llm_agent_result(self, llm: ChatOpenAI, ticket: str, code: str, image_description: str):
        retriever_code, retriever_docs = self.retriever_factory.get_retrievers()
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
        input = self.prompt_template_provider.get_prompt_template(ticket, code, image_description)

        return executor.invoke(
            {"input": input, "closure": "", "main": ""},
            {"callbacks": [self.st_cb]}
        )

    @st.spinner('Analyzing documents..')
    def get_multi_agent_system_result(self, llm: ChatOpenAI, ticket: str, code: str):
        agent_system = AgentSystem(llm)
        workflow = agent_system.build_system()

        result = workflow.invoke({
            "ticket": ticket,
            "code": code,
            "messages": []
        })

        return self._process_final_response(result)

    @st.spinner('Analyzing image..')
    def get_llm_image_describe_result(self, image_bin, ticket: str)->str:
        client = OpenAI()
        encoded_string = base64.b64encode(image_bin).decode("utf-8")
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text":  self.prompt_template_provider.get_prompt_template_for_image(ticket.__str__())
                        },
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64, {encoded_string}"},
                        },
                    ],
                }
            ],
        )

        return response.choices[0]['message']['content']

    def _process_final_response(self, workflow_output):
        final_response = next(
            msg for msg in reversed(workflow_output["messages"])
            if "APPROVED" in msg.content
        )
        return {
            "answer": final_response.content,
            "source_documents": []  # Add document tracking if needed
        }

    def _get_project_dir_structure(self):
        with open("data/documentation/baseInformation/projectDirectoryStructure.txt", "r") as f:
            dir_structure = f.readlines()
        return "\n".join(dir_structure)