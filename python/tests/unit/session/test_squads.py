import pytest
from plantangenet.squad import Squad
from plantangenet.squad.chocolate import ChocolateSquad


class DummyUpdatable:
    def __init__(self):
        self.updated = False

    async def update(self):
        self.updated = True


@pytest.mark.asyncio
async def test_vanilla_squad_add_and_get():
    sport = Squad(name="test_sport")
    obj1, obj2 = object(), object()
    sport.add('group1', obj1)
    sport.add('group1', obj2)
    group = sport.get('group1')
    assert obj1 in group and obj2 in group


@pytest.mark.asyncio
async def test_vanilla_squad_difference():
    sport = Squad(name="test_sport")
    a, b, c = object(), object(), object()
    sport.add('A', a)
    sport.add('A', b)
    sport.add('B', b)
    sport.add('B', c)
    diff = sport.difference('A', 'B')
    assert a in diff and b not in diff and c not in diff


@pytest.mark.asyncio
async def test_chocolate_squad_update():
    up = DummyUpdatable()
    down = DummyUpdatable()
    left = object()
    sport = ChocolateSquad(name="choco-berry")
    sport.add('updatables', up)
    sport.add('updatables', down)
    sport.add('common', left)
    await sport.update()
    assert up.updated
    assert down.updated
