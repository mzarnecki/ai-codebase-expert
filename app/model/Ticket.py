from app.layout.Form import Form
from app.model.TicketImage import TicketImage

class Ticket:
    def __init__(
        self,
        layout: Form,
    ):
        self.subject = layout.ticketSubject
        self.description = layout.ticketDescription
        self.url = layout.ticketUrl
        self.device = layout.ticketDevice
        self.user = layout.ticketUser
        self.code = layout.ticketCode
        self.code = self.code.replace("{", "&#123;").replace("}", "&#125;")
        self.image = None

        if layout.ticketImage  is not None:
            #read file as bytes:
            bytes_data = layout.ticketImage.getvalue()
            self.image = TicketImage(bytes_data, layout.ticketImage.name)

    def __str__(self):
        return (f'''subject: {self.subject}\n
description: {self.description}\n
url: {self.url}\n
device: {self.device}\n
user: {self.user}\n
''')


