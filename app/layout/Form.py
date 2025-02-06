import streamlit as st
class Form:
    def __init__(self):
        self.ticketSubject = st.text_input(label="Ticket subject")
        self.ticketDescription = st.text_area(label="Ticket description")
        self.ticketUrl = st.text_input(label="URL")
        self.ticketUser = st.selectbox(
            "User",
            ("guest", "registered", "premium", "admin"),
            index=None,
            placeholder="Select user type",
        )
        self.ticketDevice = st.selectbox(
            "Device type",
            ("Desktop", "Mobile"),
            index=None,
            placeholder="Select device type",
        )
        self.ticketImage =  st.file_uploader("Image")
        self.ticketCode = st.text_area(label="Related code samples")
        self.use_agent = st.radio("Use agent", options=("single-request", "agent", "multi-agent"))
        self.submitted = st.button('Submit')
