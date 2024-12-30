import os
from lib import utils
from lib.db.VectorStore import VectorStore
from lib.model.Ticket import Ticket
from lib.streaming import StreamHandler
import streamlit as st

from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationalRetrievalChain
from langchain_core.documents import Document
from langchain_core.prompts import SystemMessagePromptTemplate, ChatPromptTemplate


st.set_page_config(page_title="AI PROJECT TICKET SOLVER", page_icon="📄")
st.header('AI PROJECT TICKET SOLVER')
st.write('AI agent capable of integration new features into project and solving issues based on ticket description.')

class CustomDocChatbot:

    def __init__(self):
        utils.sync_st_session()
        self.llm = utils.configure_llm()
        self.embedding_model = utils.configure_embedding_model()

    @st.spinner('Analyzing documents..')
    def find_solution(self, ticket: str):
        document = Document(page_content=ticket)
        vectordb = VectorStore.get_vector_store(EnumDocsCollection.COMPANYHOUSE_PROJ_CODE)

        # Define retriever
        retriever = vectordb.as_retriever(
            search_type='similarity',
            search_kwargs={'k':2, 'fetch_k':4}
        )

        # Setup memory for contextual conversation
        memory = ConversationBufferMemory(
            memory_key='chat_history',
            output_key='answer',
            return_messages=True
        )

        system_message_prompt = SystemMessagePromptTemplate.from_template(
            """
            You are a chatbot tasked with solving software project issues
    
            Considering text above create solution for ticket described below.
            Write working code solution and add explanation and additional instructions related to using this code if needed. 
            {ticket}
            
            For solution use information below.
            {context}
            
            """
        )

        prompt = ChatPromptTemplate.from_messages([system_message_prompt])

        # Setup LLM and QA chain
        qa_chain = ConversationalRetrievalChain.from_llm(
            llm=self.llm,
            retriever=retriever,
            memory=memory,
            return_source_documents=True,
            verbose=False,
            combine_docs_chain_kwargs={"prompt": prompt}
        )

        return qa_chain

    @utils.enable_chat_history
    def main(self):
        with st.form("my_form"):
            ticketName = st.text_input(label="ticket name")
            ticketDescription = st.text_input(label="ticket description")
            ticketEnvironment = st.text_input(label="ticket environment")
            ticketUrl = st.text_input(label="URL")
            ticketUser = st.selectbox(
                "User",
                ("guest", "registered", "premium", "admin"),
                index=None,
                placeholder="Select user type",
            )
            ticketDevice = st.selectbox(
                "Device type",
                ("Desktop", "Mobile"),
                index=None,
                placeholder="Select device type",
            )
            ticketImage =  st.file_uploader("ticket image")
            submitted = st.form_submit_button()

            if submitted:

                if ticketImage  is not None:
                    #read file as bytes:
                    bytes_data = ticketImage .getvalue() #TODO handle file

                ticket = Ticket(
                    ticketName,
                    ticketDescription,
                    ticketEnvironment,
                    ticketUrl,
                    ticketDevice,
                    ticketUser,
                    []
                )


                qa_chain = self.find_solution(ticket.__str__())

                utils.display_msg(ticket.__str__(), 'user')

                with st.chat_message("assistant"):
                    st_cb = StreamHandler(st.empty())

                    result = qa_chain.invoke(
                        {"question":ticket.__str__()},
                        {"callbacks": [st_cb]}
                    )
                    response = result["answer"]
                    st.session_state.messages.append({"role": "assistant", "content": response})
                    utils.print_qa(CustomDocChatbot, ticket.__str__(), response)

                    # to show references
                    for  doc in result['source_documents']:
                        filename = os.path.basename(doc.metadata['source'])
                        ref_title = f":blue[Source document: {filename}]"
                        with st.popover(ref_title):
                            st.caption(doc.page_content)

if __name__ == "__main__":
    obj = CustomDocChatbot()
    obj.main()