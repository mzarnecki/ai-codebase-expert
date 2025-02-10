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
from openai import OpenAI as OpenAIModel

from app import utils
from app.db.CodeGraph import CodeGraph
from app.llm.PromptTemplateProvider import PromptTemplateProvider

from langchain.agents import AgentExecutor

from app.llm.agent.AgentSystem import AgentSystem
from app.llm.retriever.RetrieverFactory import RetrieverFactory
from app.streaming import StreamHandler

class LLMChainProvider:

    def __init__(self, programming_language: str, framework: str, project_description: str):
        self.retriever_factory = RetrieverFactory()
        self.prompt_template_provider = PromptTemplateProvider(programming_language, framework, project_description)

    @st.spinner('Analyzing documents...')
    def get_llm_preparation_chain_result(
            self,
            llm: ChatOpenAI,
            ticket: str,
            code: str,
            image_description: str
    ):
        self.st_cb = StreamHandler(st.empty())
        # Setup memory for contextual conversation
        memory = ConversationBufferMemory()

        # Setup LLM and QA chain
        llm_chain = ConversationChain(
            llm=llm,
            memory=memory,
            verbose=False,
        )
        prompt_message = self.prompt_template_provider.get_prompt_RAG(
            ticket,
            code,
            self._get_project_dir_structure()
        )

        if code:
            prompt_message = prompt_message + "\n\nRELATED CODE:\n" + code

        if image_description:
            prompt_message = prompt_message + "\n\nIMAGE DESCRIPTION:\n" + image_description

        prompt = {"input": prompt_message}

        result = llm_chain.invoke(prompt)

        return result

    @st.spinner('Resolving issue..')
    def get_llm_conversational_chain_result(self, llm: ChatOpenAI, ticket: str, code: str, image_description: str):
        self.st_cb = StreamHandler(st.empty())
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

    @st.spinner('Resolving issue..')
    def get_llm_agent_result(self, llm: ChatOpenAI, ticket: str, code: str, image_description: str):
        self.st_cb = StreamHandler(st.empty())
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
        executor = AgentExecutor.from_agent_and_tools(
            agent=agent,
            tools=tools,
            handle_parsing_errors=True,
            max_execution_time=180,
            return_source_documents=True,
            early_stopping_method="generate",
            verbose=True
        )
        input = self.prompt_template_provider.get_prompt_template(ticket, code, image_description)

        return executor.invoke(
            {"input": input, "closure": "", "main": ""},
            {"callbacks": [self.st_cb]}
        )

    @st.spinner('Resolving issue..')
    def get_multi_agent_system_result(self, llm: ChatOpenAI, ticket: str, code: str, image_description: str):

        agent_system = AgentSystem(llm, self.prompt_template_provider, self.retriever_factory)
        workflow = agent_system.build_system(ticket, self._get_project_dir_structure(), code, image_description)

        result = workflow.invoke({
            "ticket": ticket,
            "code": code,
            "messages": [],
            "iteration_count": 0
        })

        return self._process_final_response(result)

    @st.spinner('Analyzing image..')
    def get_llm_image_describe_result(self, image_bin, ticket: str)->str:
        client = OpenAIModel()
        encoded_string = base64.b64encode(image_bin).decode("utf-8")
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text":  self.prompt_template_provider.get_prompt_template_for_image(ticket)
                        },
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64, {encoded_string}"},
                        },
                    ],
                }
            ],
        )

        return response.choices[0].message.content

    def _process_final_response(self, workflow_output):
        # Extract messages from the output state
        messages = workflow_output.get("messages", [])
        print(messages)

        if not messages:
            return {"answer": "No response generated by the agents.", "source_documents": []}

        # Try to find an approved message
        # approved_messages = [msg for msg in reversed(messages) if "APPROVED" in msg.content]

        # if approved_messages:
        #     final_response = approved_messages[-2]  # Get the most recent approved message
        # else:
        #     # Fallback: Get the last message in the list if no "APPROVED" message exists
        final_response = messages[-2]

        utils.display_msg("FINAL RESPONSE:\n" + final_response.content, "assistant")

        return {
            "answer": final_response.content,
            "source_documents": []  # Add document tracking if needed
        }


    def _get_project_dir_structure(self):
        with open("data/documentation/baseInformation/projectDirectoryStructure.txt", "r") as f:
            dir_structure = f.readlines()
        return "\n".join(dir_structure)