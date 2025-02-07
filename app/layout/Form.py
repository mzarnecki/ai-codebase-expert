import streamlit as st
class Form:
    def __init__(self):
        col1, col2, col3 = st.columns(3)
        with col1:
            self.ticket_subject = st.text_input(label="Ticket subject")
            self.ticket_description = st.text_area(label="Ticket description")
            self.ticket_url = st.text_input(label="URL")
            self.ticket_user = st.selectbox(
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

        with col2:
            self.ticket_image =  st.file_uploader("Image")
            self.ticket_code = st.text_area(label="Related code samples")
            self.use_agent = st.radio("Use agent", options=("single-request", "agent", "multi-agent"))
            self.submitted = st.button('Submit')

        with col3:
            self.jira_task = st.text_input(label="Jira task", placeholder="MHDE-1234")
            self.submit_jira = st.button('Submit Jira ticket')
