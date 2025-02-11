from app.layout.Form import Form
from app.model.TicketImage import TicketImage

class Ticket:
    def __init__(
        self,
        layout: Form,
    ):
        self.subject = layout.ticket_subject
        self.description = layout.ticket_description
        self.url = layout.ticket_url
        self.device = layout.ticketDevice
        self.user = layout.ticket_user
        self.code = layout.ticket_code
        self.code = self.code.replace("{", "&#123;").replace("}", "&#125;")
        self.additional_instruction = layout.additional_instruction
        self.image = None

        if layout.ticket_image  is not None:
            #read file as bytes:
            bytes_data = layout.ticket_image.getvalue()
            self.image = TicketImage(bytes_data, layout.ticket_image.name)

    def __str__(self):
        message = f"subject: {self.subject}\n description: {self.description}\n\n"
        if self.user:
            message += f"User: {self.user}\n\n"
        if self.url:
            message += f"URL: {self.url}\n\n"
        if self.device:
            message += f"Device: {self.device}\n\n"
        if self.additional_instruction:
            message += f"Additional instructions to be handled by LLM: {self.additional_instruction}\n"
        return message


