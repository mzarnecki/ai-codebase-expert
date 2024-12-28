
from langchain.agents import AgentType
from langchain_community.agent_toolkits import FileManagementToolkit, JiraToolkit, SQLDatabaseToolkit
from dotenv import load_dotenv, find_dotenv
from langchain.agents import initialize_agent
from langchain_community.tools import DuckDuckGoSearchResults
from langchain_community.utilities import JiraAPIWrapper
from langchain_community.utilities.dataforseo_api_search import DataForSeoAPIWrapper
from langchain_core.tools import Tool
from langchain_openai import ChatOpenAI
from langchain_community.tools.riza.command import ExecPython

from lib.agent.tools.FrameworkDocumentation import FrameworkDocumentation
from lib.agent.tools.ProjectCode import ProjectCode
from lib.agent.tools.ProjectDocumentation import ProjectDocumentation

import sqlite3
import requests
from langchain_community.utilities.sql_database import SQLDatabase
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool


class TicketSolverAgent:

    def run(self):
        load_dotenv(find_dotenv())

        llm = ChatOpenAI(model_name="gpt-4o", temperature=0)

        # filesystem https://python.langchain.com/docs/integrations/tools/filesystem/
        filesToolkit = FileManagementToolkit(
            root_dir=str('data')
        )  # If you don't provide a root_dir, operations will default to the current working directory
        filesTools = filesToolkit.get_tools()

        # duckduckgosearch https://python.langchain.com/docs/integrations/tools/ddg/

        # jira toolkit https://python.langchain.com/docs/integrations/tools/jira/
        jira = JiraAPIWrapper()
        jiraToolkit = JiraToolkit.from_jira_api_wrapper(jira)
        jiraTools = jiraToolkit.get_tools()

        # SEO tool https://python.langchain.com/docs/integrations/tools/dataforseo/
        search = DataForSeoAPIWrapper(
            top_count=3,
            json_result_types=["organic"],
            json_result_fields=["title", "description", "type"],
        )
        SEOTool = Tool(
            name="google-search-answer",
            description="My new answer tool",
            func=search.run,
        )

        # Riza code interpreter (PHP) https://python.langchain.com/docs/integrations/tools/riza/

        # SQLDatabase Toolkit https://python.langchain.com/docs/integrations/tools/sql_database/
        def get_engine_for_chinook_db():
            """Pull sql file, populate in-memory database, and create engine."""
            url = "https://raw.githubusercontent.com/lerocha/chinook-database/master/ChinookDatabase/DataSources/Chinook_Sqlite.sql"
            response = requests.get(url)
            sql_script = response.text

            connection = sqlite3.connect(":memory:", check_same_thread=False)
            connection.executescript(sql_script)
            return create_engine(
                "sqlite://",
                creator=lambda: connection,
                poolclass=StaticPool,
                connect_args={"check_same_thread": False},
            )


        engine = get_engine_for_chinook_db()

        db = SQLDatabase(engine)
        SQLToolkit = SQLDatabaseToolkit(db=db, llm=llm)
        SQLTools = SQLToolkit.get_tools()


        tools = [FrameworkDocumentation(), ProjectCode(), ProjectDocumentation(), DuckDuckGoSearchResults(),
                 ExecPython(), SEOTool] + filesTools + jiraTools + SQLTools
        agent = initialize_agent(tools, llm, agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION, verbose=True)
        agent.run("Find some bug in project and propose solution or improvement")