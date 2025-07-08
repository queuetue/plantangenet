import pytest
from plantangenet.core import RegistrableComponent, ComponentRegistry, ComponentRegistryMixin


class DummyComponent(RegistrableComponent):
    pass


class DummyManager(ComponentRegistryMixin):
    def __init__(self):
        super().__init__()


def test_register_and_unregister_component():
    registry = ComponentRegistry()
    comp = DummyComponent(name="foo")
    registry.register(comp)
    assert comp in registry.all_components()
    registry.unregister(comp)
    assert comp not in registry.all_components()


def test_lookup_by_name_and_type():
    registry = ComponentRegistry()
    comp1 = DummyComponent(name="foo")
    comp2 = DummyComponent(name="bar")
    registry.register(comp1)
    registry.register(comp2)
    assert registry.get_by_name("foo") is comp1
    assert comp1 in registry.get_by_type(DummyComponent)


def test_name_conflict_error():
    registry = ComponentRegistry()
    comp1 = DummyComponent(name="foo")
    comp2 = DummyComponent(name="foo")
    registry.register(comp1)
    registry.register(comp2)
    assert any("Name conflict" in err for err in comp2.errors)


def test_registry_mixin_add_remove():
    mgr = DummyManager()
    comp = DummyComponent(name="baz")
    mgr.add_component(comp)
    assert mgr.get_component("baz") is comp
    mgr.remove_component(comp)
    assert mgr.get_component("baz") is None


def test_registry_mixin_all_components():
    mgr = DummyManager()
    comp1 = DummyComponent(name="a")
    comp2 = DummyComponent(name="b")
    mgr.add_component(comp1)
    mgr.add_component(comp2)
    all_names = {c.name for c in mgr.all_components()}
    assert all_names == {"a", "b"}
