from lib.model.TicketImage import TicketImage

class Ticket:
    def __init__(self, name: str, environment: str, description: str, images: list[TicketImage]):
        self.name = name
        self.environment = environment
        self.description = description
        self.images = images


