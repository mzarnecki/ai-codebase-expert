import io
class StreamToStreamlit: # Helper class to redirect stdout to Streamlit
    def __init__(self, container):
        self.container = container
        self.text_IO = io.StringIO()

    def write(self, output):
        # Instead of Streamlit, just print to console for now
        print(output, end="") # Print to standard output, which will be visible in your console

    def flush(self):
        pass # For compatibility, no action needed