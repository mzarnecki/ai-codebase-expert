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
        self.image = None

        if layout.ticket_image  is not None:
            #read file as bytes:
            bytes_data = layout.ticket_image.getvalue()
            self.image = TicketImage(bytes_data, layout.ticket_image.name)

    def __str__(self):
        return (f'''subject: {self.subject}\n
description: {self.description}\n
url: {self.url}\n
device: {self.device}\n
user: {self.user}\n
''')


