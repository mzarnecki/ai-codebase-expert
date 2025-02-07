import os
from app import utils
from app.layout.Form import Form
from app.llm.LLMChainProvider import LLMChainProvider
from app.model.Ticket import Ticket
import streamlit as st
from dotenv import load_dotenv, find_dotenv
from jira import JIRA

st.set_page_config(page_title="CODEBASE EXPERT", page_icon="🤖")
utils.styleLayout()
st.header('CODEBASE EXPERT')
st.write('AI llm capable of integration new features into project and solving issues based on ticket description.')

PROGRAMMING_LANGUAGE = 'PHP' #replace with language of your code base
FRAMEWORK = 'Yii2' #replace with framework related to your code base
PROJECT_DESCRIPTION = 'website application' #replace with description of your application

class CodebaseChatbot:

    def __init__(self):
        load_dotenv(find_dotenv())
        utils.sync_st_session()
        self.llm = utils.configure_llm()
        self.embedding_model = utils.configure_embedding_model()
        self.llm_chain_provider = LLMChainProvider(
            programming_language=PROGRAMMING_LANGUAGE,
            framework=FRAMEWORK,
            project_description=PROJECT_DESCRIPTION
        )

    @utils.enable_chat_history
    def main(self):
        form = Form()

        if form.submitted:
            ticket = Ticket(form)
            self._process_ticket(ticket, form)

        if form.submit_jira:
            ticket = Ticket(form)
            self._get_jira_task(ticket, form.jira_task)
            self._process_ticket(ticket, form)


    def _get_jira_task(self, ticket: Ticket, task_no: str):
        # domain name link. yourdomainname.atlassian.net
        jiraOptions = {'server': os.environ.get('JIRA_SERVER')}
        jira = JIRA(options=jiraOptions, basic_auth=(os.environ.get('JIRA_USER'), os.environ.get('JIRA_PASS')))

        # Search all issues mentioned against a project name.
        for singleIssue in jira.search_issues(jql_str=f"project = {os.environ.get('JIRA_PROJECT')} AND issue={task_no}"):
            print('{}: {}:{}'.format(singleIssue.key, singleIssue.fields.summary,
                                     singleIssue.fields.reporter.displayName))
            ticket.subject = singleIssue.fields.summary
            ticket.description = singleIssue.fields.description
            return

    def _process_ticket(self, ticket: Ticket, form: Form):
        utils.display_msg("Ticket summary:\n\n" + ticket.__str__(), 'user')

        image_description = self._describe_attached_image(ticket)
        if image_description:
            utils.display_msg("Image description:\n" + image_description, "assistant")

        rag_output = self._get_concepts_with_RAG_for_the_task(ticket, image_description)
        utils.display_msg("RAG output:\n" + rag_output, "assistant")

        result = self._provide_solution_with_selected_LLM_chain(form, ticket, rag_output, image_description)
        self._display_response_and_source_documents(result, ticket, rag_output)

    def _describe_attached_image(self, ticket: Ticket) -> str:
        if ticket.image:
            image_description = self.llm_chain_provider.get_llm_image_describe_result(ticket.image.image_binary, ticket.__str__())
            print(f"Image description: {image_description}")
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

    def _provide_solution_with_selected_LLM_chain(self, form: Form, ticket: Ticket, rag_output: str, image_description: str) -> dict:
        if form.use_agent == 'agent':
            result = self.llm_chain_provider.get_llm_agent_result(
                self.llm,
                ticket.__str__() + rag_output,
                ticket.code,
                image_description
            )
        elif form.use_agent == 'multi-agent':
            result = self.llm_chain_provider.get_multi_agent_system_result(
                self.llm,
                ticket.__str__() + rag_output,
                ticket.code,
                image_description
            )
        else:
            result = self.llm_chain_provider.get_llm_conversational_chain_result(
                self.llm,
                ticket.__str__() + rag_output,
                ticket.code,
                image_description
            )
        return result

    def _display_response_and_source_documents(self, result: dict, ticket: Ticket, rag_output: str) -> None:
        if 'answer' in result:
            response = result["answer"]
        else:
            response = result["output"]

        utils.print_qa(CodebaseChatbot, ticket.__str__(), rag_output, response)
        st.session_state.messages.append({"role": "assistant", "content": response})

        # to show references
        if 'source_documents' in result:
            print('Source documents:', result['source_documents'])
            for doc in result['source_documents']:
                filename = os.path.basename(doc.metadata['source'])
                ref_title = f":blue[Source document: {filename}]"
                with st.popover(ref_title):
                    st.caption(doc.page_content)


if __name__ == "__main__":
    obj = CodebaseChatbot()
    obj.main()