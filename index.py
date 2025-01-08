import os
from app import utils
from app.layout.Layout import Layout
from app.llm.LLMChainProvider import LLMChainProvider
from app.model.Ticket import Ticket
import streamlit as st
from dotenv import load_dotenv, find_dotenv

st.set_page_config(page_title="COMPANYHOUSE CODEBASE EXPERT", page_icon="📄")
st.header('COMPANYHOUSE CODEBASE EXPERT')
st.write('AI llm capable of integration new features into project and solving issues based on ticket description.')

class CodebaseChatbot:

    def __init__(self):
        load_dotenv(find_dotenv())
        utils.sync_st_session()
        self.llm = utils.configure_llm()
        self.embedding_model = utils.configure_embedding_model()

    @utils.enable_chat_history
    def main(self):
        layout = Layout()

        if layout.submitted:
            ticket = Ticket(layout)

            utils.display_msg(ticket.__str__(), 'user')

            provider = LLMChainProvider()
            with st.chat_message("assistant"):
                resultRag = provider.getLLMPrparationChainResult(self.llm, ticket.__str__(), ticket.code)
                responseRag = resultRag['response']
                print(responseRag)
                print("\n")
                ragOutput = responseRag.replace('{', '{{').replace('}', '}}')
                if layout.useAgent:
                    result = provider.getLLMAgent(self.llm,  ticket.__str__() + ragOutput, ticket.code)
                else:
                    result = provider.getLLMConversationalChainResult(self.llm,  ticket.__str__() + ragOutput, ticket.code)
                response = result["answer"]
                st.session_state.messages.append({"role": "assistant", "content": response})
                utils.print_qa(CodebaseChatbot,  ticket.__str__(), responseRag, response)

                # to show references
                print(result['source_documents'])
                for  doc in result['source_documents']:
                    filename = os.path.basename(doc.metadata['source'])
                    ref_title = f":blue[Source document: {filename}]"
                    with st.popover(ref_title):
                        st.caption(doc.page_content)

if __name__ == "__main__":
    obj = CodebaseChatbot()
    obj.main()