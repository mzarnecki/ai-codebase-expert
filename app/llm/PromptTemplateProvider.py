from langchain_core.prompts import SystemMessagePromptTemplate

class PromptTemplateProvider(object):
    def getPromptTemplate(ticket: str):
        return SystemMessagePromptTemplate.from_template(
            """
            You are a chatbot tasked with solving software project issues.
            The project is a website companyhouse.de and it's written in PHP language.
    
            Considering above create solution for ticket described below.
            Write working code solution and add explanation and additional instructions related to using this code if needed. 
            """ + ticket + """
            
            For solution use information from project code and documentation below.
            {context}
            
            """,
            )

    def getPromptRAG(ticket: str):
        return SystemMessagePromptTemplate.from_template(
            """
            You are a chatbot tasked with solving software project issues.
            The project is a website companyhouse.de and it's written in PHP language using Yii2 framework.
            Prepare message that will be used for sematic search in database for project code and project documentation.
            Prepare message based on issue description below. Say which files should be checked.
            """ + ticket + """
            """,
            )