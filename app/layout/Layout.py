import streamlit as st
class Layout:
    def __init__(self):
        self.ticketSubject = st.text_input(label="ticket subject")
        self.ticketDescription = st.text_area(label="ticket description")
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
        self.useAgent = st.checkbox("Use agent")
        self.submitted = st.button('Submit')
