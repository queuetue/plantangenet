from typing import Protocol


class Trader(Protocol):
    async def buy(self, world, player, contract, minimum, maximum, price):
        """
        Attempt to purchase a resource using an existing open SELL contract.

        - `world`: The game state or environment.
        - `player`: The player object invoking the action.
        - `contract`: The contract offering the resource.
        - `minimum`, `maximum`: Desired quantity range.
        - `price`: Price per unit the agent is willing to pay.

        Fails if conditions are invalid (insufficient funds, invalid contract).
        """

    async def sell(self, world, player, contract, minimum, maximum, price):
        """
        Attempt to fulfill an open BUY contract by selling a resource.

        - `world`: The game state or environment.
        - `player`: The player object invoking the action.
        - `contract`: The contract requesting the resource.
        - `minimum`, `maximum`: Desired quantity range.
        - `price`: Price per unit the agent demands.

        Fails if conditions are invalid (insufficient inventory, invalid contract).
        """

    async def issue(self, world, player, type, resource, amount, price, contract=None):
        """
        Create a new market contract.

        - `type`: "buy" or "sell".
        - `resource`: The resource or good in question.
        - `amount`: Quantity to buy/sell.
        - `price`: Price per unit.
        - `contract`: Optional pre-existing contract to amend.

        Resources or credits may be reserved in escrow until fulfillment.
        """

    async def cancel(self, world, player, contract):
        """
        Cancel an open contract the player issued.

        - `contract`: The contract to cancel.

        Typically returns escrow minus a cancellation penalty.
        """

    async def modify(self, world, player, contract, price):
        """
        Adjust the price of an open contract.

        - `contract`: The contract to modify.
        - `price`: The new price per unit.

        Rules may restrict increases/decreases based on contract type.
        """

    async def travel(self, world, player, destination):
        """
        Move to a new location.

        - `destination`: Target location identifier.

        Travel time/cost is usually determined by the environment.
        """

    async def idle(self, world, player):
        """
        Do nothing for one game turn.

        Used when the agent chooses to pass or wait.
        """
