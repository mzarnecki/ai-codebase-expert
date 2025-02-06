import os
from app import utils
from app.layout.Form import Form
from app.llm.LLMChainProvider import LLMChainProvider
from app.model.Ticket import Ticket
import streamlit as st
from dotenv import load_dotenv, find_dotenv

st.set_page_config(page_title="CODEBASE EXPERT", page_icon="📄")
st.header('CODEBASE EXPERT')
st.write('AI llm capable of integration new features into project and solving issues based on ticket description.')

class CodebaseChatbot:

    def __init__(self):
        load_dotenv(find_dotenv())
        utils.sync_st_session()
        self.llm = utils.configure_llm()
        self.embedding_model = utils.configure_embedding_model()
        self.llm_chain_provider = LLMChainProvider()
        self.form = Form()

    @utils.enable_chat_history
    def main(self):
        if self.form.submitted:
            ticket = Ticket(self.form)
            image_description = self._describe_attached_image(ticket)
            utils.display_msg(ticket.__str__(), 'user')
            ragOutput = self._get_concepts_with_RAG_for_the_task(ticket, image_description)

            with st.chat_message("assistant"):
                result = self._provide_solution_with_selected_LLM_chain(ticket, ragOutput, image_description)
                self._display_response_and_source_documents(result, ticket, ragOutput)

    def _describe_attached_image(self, ticket: Ticket) -> str:
        if ticket.image:
            image_description = self.llm_chain_provider.get_llm_image_describe_result(ticket.image)
            print(f"Image description: {ticket.image}")
            return image_description
        return ''

    def _get_concepts_with_RAG_for_the_task(self, ticket: Ticket, image_description: str) -> str:
        result_rag = self.llm_chain_provider.get_llm_preparation_chain_result(
            self.llm,
            ticket.__str__(),
            ticket.code,
            image_description
        )
        response_rag = result_rag['response']
        print(f'response_rag\n')
        rag_output = response_rag.replace('{', '{{').replace('}', '}}')
        return rag_output

    def _provide_solution_with_selected_LLM_chain(self, ticket: Ticket, ragOutput: str) -> dict:
        if self.form.use_agent == 'agent':
            result = self.llm_chain_provider.get_llm_agent_result(
                self.llm,
                ticket.__str__() + ragOutput,
                ticket.code
            )
        elif self.form.use_agent == 'multi-agent':
            result = self.llm_chain_provider.get_multi_agent_system_result(
                self.llm,
                ticket.__str__()  + ragOutput,
                ticket.code
            )
        else:
            result = self.llm_chain_provider.get_llm_conversational_chain_result(
                self.llm,
                ticket.__str__() + ragOutput,
                ticket.code
            )
        return result

    def _display_response_and_source_documents(self, result: dict, ticket: Ticket, ragOutput: str) -> None:
        if 'answer' in result:
            response = result["answer"]
        else:
            response = result["output"]
        utils.print_qa(CodebaseChatbot,  ticket.__str__(), ragOutput, response)
        st.session_state.messages.append({"role": "assistant", "content": response})

        # to show references
        if 'source_document' in result:
            print(result['source_documents'])
            for  doc in result['source_documents']:
                filename = os.path.basename(doc.metadata['source'])
                ref_title = f":blue[Source document: {filename}]"
                with st.popover(ref_title):
                    st.caption(doc.page_content)


if __name__ == "__main__":
    obj = CodebaseChatbot()
    obj.main()