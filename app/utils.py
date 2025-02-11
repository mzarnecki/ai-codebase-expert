import os
import streamlit as st
from streamlit.logger import get_logger
from langchain_openai import ChatOpenAI
from langchain_community.embeddings.fastembed import FastEmbedEmbeddings

logger = get_logger('Langchain-Chatbot')

#decorator
def enable_chat_history(func):
    if os.environ.get("OPENAI_API_KEY"):

        # to clear chat history after swtching chatbot
        current_page = func.__qualname__
        if "current_page" not in st.session_state:
            st.session_state["current_page"] = current_page
        if st.session_state["current_page"] != current_page:
            try:
                st.cache_resource.clear()
                del st.session_state["current_page"]
                del st.session_state["messages"]
            except:
                pass

        # to show chat history on ui
        if "messages" not in st.session_state:
            st.session_state["messages"] = []
        for msg in st.session_state["messages"]:
            st.chat_message(msg["role"]).write(msg["content"])

    def execute(*args, **kwargs):
        func(*args, **kwargs)
    return execute

def display_msg(msg, author):
    """Method to display message on the UI

    Args:
        msg (str): message to display
        author (str): author of the message -user/assistant
    """
    st.session_state.messages.append({"role": author, "content": msg})
    st.chat_message(author).write(msg)

def configure_llm() -> ChatOpenAI:
    llm = ChatOpenAI(model_name='gpt-4o', temperature=0, streaming=True)
    return llm

def print_qa(cls, question: str, concepts: str, answer: str):
    log_str = "\nUsecase: {}\nQuestion: {}\nConcepts: {}\nAnswer: {}\n" + "------"*10
    logger.info(log_str.format(cls.__name__, question, concepts, answer))

@st.cache_resource
def configure_embedding_model():
    embedding_model = FastEmbedEmbeddings(model_name="BAAI/bge-small-en-v1.5")
    return embedding_model

def sync_st_session():
    for k, v in st.session_state.items():
        st.session_state[k] = v


def styleLayout():
    st.set_page_config(page_title="CODEBASE EXPERT", page_icon="🤖", layout='wide')
    st.markdown("""
    <style>
        div[data-testid="column"]:nth-child(3) {
            border: 2px solid gray;
            padding: 10px;
        }
    /* General styles */
    body {
        background-color: #1e1e2e;
        color: #ffffff;
        font-family: 'Inter', sans-serif;
    }
    
    p, h2, h3 {
        color: #fff;
    }
    
    img {
      display: inline-block;
      margin-left: 20%;
      margin-right: auto;
      width: 80%;
    }
    
    /* Styling main container */
    .stApp {
        background-color: #1e1e2e;
        color: #ffffff;
    }
    
    /* Sidebar */
    .stSidebar {
        background-color: #282a36;
        color: #ffffff;
    }
    
    /* Header */
    .stHeader {
        background-color: #1e1e2e;
        border-bottom: 2px solid #44475a;
        padding: 10px;
        color: #ffffff;
    }
    
    /* Buttons */
    button, .stButton > button {
        background-color: #000 !important;
        color: #ffffff !important;
        border-radius: 8px !important;
        font-size: 16px !important;
        padding: 10px 20px !important;
        transition: 0.3s;
    }
    button:hover, .stButton > button:hover {
        background-color: #6a0dad !important;
        color: #ffffff !important;
    }
    
    /* Input fields */
    .stTextInput > label, .stTextArea > label, .stSelectbox > label, .stRadio > label {
        color: #ffffff !important;
        font-weight: bold !important;
    }
    
    .stTextInput > div > div > input, .stTextArea > div > div > textarea, .stSelectbox > div > div > select {
        background-color: #44475a !important;
        color: #ffffff !important;
        border-radius: 6px !important;
        border: none !important;
    }
    
    /* Fix for placeholder text visibility */
    .stTextInput > div > div > input::placeholder, .stTextArea > div > div > textarea::placeholder, .stSelectbox > div > div > select::placeholder {
        color: #b0b0b0 !important;
    }
    
    /* File uploader */
    .stFileUploader > div {
        background-color: #44475a !important;
        color: #ffffff !important;
        border: 2px dashed #ff79c6 !important;
        border-radius: 10px !important;
    }
    
    /* Cards and sections */
    .stMarkdown, .stDataFrame, .stTextArea, .stTextInput, .stSelectbox, .stButton, .stRadio, .stFileUploader {
        background-color: #282a36 !important;
        border-radius: 10px !important;
        padding: 10px !important;
        margin-bottom: 15px !important;
        color: #ffffff !important;
    }
    
    /* Jira Task Box */
    .stTextInput .jira-task {
        background-color: #44475a !important;
        border-radius: 8px !important;
        padding: 10px !important;
        font-weight: bold !important;
        color: #ffffff !important;
    }
    
    /* Highlight code block */
    .stCodeBlock {
        background-color: #282a36 !important;
        border-radius: 6px !important;
        padding: 10px !important;
        color: #ffffff !important;
    }
    
    /* Use agent selection */
    .stRadio > div {
        background-color: #282a36 !important;
        border-radius: 6px !important;
        padding: 10px !important;
        color: #ffffff !important;
    }
    
    /* Column layout adjustments */
    .css-1y4p8pa {
        display: flex;
        gap: 20px;
    }
    
    /* Hover Effects */
    .stButton:hover, .stSelectbox:hover, .stTextInput:hover, .stTextArea:hover {
        box-shadow: 0px 0px 10px #ff79c6 !important;
    }

    </style>
    """, unsafe_allow_html=True)