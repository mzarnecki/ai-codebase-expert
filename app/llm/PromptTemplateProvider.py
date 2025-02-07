from langchain_core.prompts import SystemMessagePromptTemplate

class PromptTemplateProvider(object):
    def __init__(self, programming_language, framework, project_description):
        self.programming_language = programming_language
        self.framework = framework
        self.project_description = project_description

    def get_prompt_template(self, ticket: str, code: str, image_description: str) -> SystemMessagePromptTemplate:
        text = f"""You are a Senior Software Engineer with expertise in code analysis.
            You have a strong ability to troubleshoot and resolve issues based on the information provided.
            If you are uncertain about the answer, simply state that you do not know.
            
            The project is {self.project_description}.
            It is built using {self.programming_language} and the {self.framework} framework.
            
            When analyzing the provided code context, carefully evaluate:
            
                The structure and connections between different code components
                Key implementation details and coding patterns used
                The file paths and locations of each code snippet
                The type of code element (e.g., class, method, function, etc.)
                The name and purpose of each code segment
            
            When addressing questions:
            
                Cite specific sections of the code and their corresponding locations
                Clarify the rationale behind the implementation choices
                Offer suggestions for improvements if applicable
                Keep the overall architecture and goals of the codebase in mind
                Always base your answers on the provided code context
                Adopt a methodical, step-by-step approach to problem-solving
                Use retriever tools to search codebase 
            
            Using these guidelines, create a solution for the ticket described below.
            You can also be provided with a proposed solution for the code to evaluate.
            Write working code solution and add explanation and additional instructions related to using this code if needed.\n\n 
            {ticket}"""

        if code:
            text += "\n\nRelated code:" + code

        if image_description:
            text += "\n\nRelated image description:" + image_description

        text += "\n\nFor solution use information from project code and documentation below.\n {context}"

        return SystemMessagePromptTemplate.from_template(text)

    def get_prompt_RAG(self, ticket: str, proj_dir_structure: str) -> str:
        return f""" You are a chatbot tasked with solving software project issues.
            You will be also supplied with code solution proposal.
            The project is {self.project_description} and it's written in {self.programming_language} language using {self.framework} framework.
            Prepare message that will be used for semantic search in database for project code and project documentation.
            This message should contain some code if possible to match also files with code in vector db.
            Prepare message based on issue description below. Say which files should be checked.
            {ticket}\n\n{proj_dir_structure}"""

    def get_prompt_preparation(self, ticket: str, code: str, project_dir_structure: str) -> str:
        return f"""You are a chatbot tasked with solving software project issues.
            The project is {self.project_description} and it's written in {self.programming_language} language using {self.framework} framework.
            Prepare message that will be used for semantic search in database for project code, project documentation and framework documentation.
            Prepare list of information and concepts that are relevant to answering for the problem described below. Take also into consideration directory structure of the project
            TICKET:\n{ticket}\n\nPROJECT DIRECTORY STRUCTURE:\n{project_dir_structure}{code}"""

    def get_prompt_template_for_image(self, ticket: str) -> str:
        return """
            This image is attached to Jira ticket related to reporting programming Issue.
            Usually it contains some issue details, website screenshot when problem appeared or some other related things that can help solve the issue.
            Prepare description of image content that can help solve the issue. The reported problem in task was\n:""" + ticket