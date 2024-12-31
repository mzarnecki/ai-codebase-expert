import os
from app import utils
from app.layout.Layout import Layout
from app.llm.LLMChainProvider import LLMChainProvider
from app.model.Ticket import Ticket
import streamlit as st

st.set_page_config(page_title="AI PROJECT TICKET SOLVER", page_icon="📄")
st.header('AI PROJECT TICKET SOLVER')
st.write('AI llm capable of integration new features into project and solving issues based on ticket description.')

class CustomDocChatbot:

    def __init__(self):
        utils.sync_st_session()
        self.llm = utils.configure_llm()
        self.embedding_model = utils.configure_embedding_model()

    @utils.enable_chat_history
    def main(self):
        layout = Layout()

        if layout.submitted:
            ticket = Ticket(layout)

            utils.display_msg(ticket.__str__(), 'user')

            with st.chat_message("assistant"):
                result = LLMChainProvider.getLLMConversationalChainResult(self.llm, ticket.__str__())
                # result = LLMChainProvider.getLLMAgent(self.llm, ticket.__str__())
                response = result["answer"]
                st.session_state.messages.append({"role": "assistant", "content": response})
                utils.print_qa(CustomDocChatbot, ticket.__str__(), response)

                # to show references
                print(result['source_documents'])
                for  doc in result['source_documents']:
                    filename = os.path.basename(doc.metadata['source'])
                    ref_title = f":blue[Source document: {filename}]"
                    with st.popover(ref_title):
                        st.caption(doc.page_content)

if __name__ == "__main__":
    obj = CustomDocChatbot()
    obj.main()