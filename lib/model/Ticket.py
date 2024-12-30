from lib.model.TicketImage import TicketImage

class Ticket:
    def __init__(
        self,
        subject: str,
        environment: str,
        description: str,
        url: str,
        device: str,
        user: str,
        images: list[TicketImage],
    ):
        self.subject = subject
        self.environment = environment
        self.description = description
        self.url = url
        self.device = device
        self.user = user
        self.images = images

    def __str__(self):
        return (f'''subject: {self.subject}\n
environment: {self.environment}\n
description: {self.description}\n
url: {self.url}\n
device: {self.device}\n
user: {self.user}\n
''')


