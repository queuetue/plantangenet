BUY, SELL = range(2)

material_names = set((
    'fuel ore',
    'medicine',
    'minerals',
    'robotics',
))


class Contract(object):
    """
    Represents a market contract for buying or selling resources.

    Attributes:
        id (int): Unique identifier for the contract.
        turn_created (int): The turn when the contract was created.
        planet (Planet): The planet associated with the contract.
        owner (Player): The player who owns the contract.
        type (int): Type of contract, either BUY (0) or SELL (1).
        material (str): The resource or good involved in the contract.
        amount (int): Quantity of the resource to buy or sell.
        price (int): Price per unit of the resource in credits.
    """

    def __init__(self):
        self.id = 0
        self.turn_created = 0
        self.planet = None
        self.owner = None
        self.type = BUY
        self.material = ''
        self.amount = 0
        self.price = 0

    def __repr__(self):
        r = (
            str(self.id).ljust(4),
            self.planet.name.ljust(11),
            ('SELL' if self.type else 'BUY').ljust(5),
            self.material.ljust(12),
            str(self.amount).rjust(5),
            (str(self.price)+'cR').rjust(5)
        )
        return '%s %s %s %s %s %s' % r
