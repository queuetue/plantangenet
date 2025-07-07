import pytest
import asyncio
from plantangenet.tournament.tournament import Tournament


class DummyPlayer:
    def __init__(self, name):
        self.name = name


class DummyGame:
    def __init__(self, game_id, p1, p2):
        self.game_id = game_id
        self.p1 = p1
        self.p2 = p2
        self.played = False
        self.winner = p1.name

    async def play(self):
        self.played = True
        return self.winner


def dummy_game_factory(game_id, p1, p2):
    return DummyGame(game_id, p1, p2)


@pytest.mark.asyncio
async def test_tournament_run():
    players = [DummyPlayer("alice"), DummyPlayer("bob")]
    tournament = Tournament(players, dummy_game_factory,
                            num_rounds=2, games_per_round=1)
    await tournament.run()
    assert tournament.games_played == 2
