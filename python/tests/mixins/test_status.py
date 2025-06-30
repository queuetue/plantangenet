import pytest
from plantangenet.mixins.status import watch
from plantangenet.mixins.status.mixin import StatusMixin


class Dummy(StatusMixin):
    count: int = watch(default=0)


class SensitiveDummy(StatusMixin):
    secret: str = watch(default="topsecret", sensitive=True)


class HiddenDummy(StatusMixin):
    hidden: int = watch(default=123, include_in_dict=False)


def test_tracked_fields_registration():
    assert "count" in Dummy._status_tracked_fields


def test_default_value():
    d = Dummy()
    assert d.count == 0


def test_set_and_get_value():
    d = Dummy()
    d.count = 5
    assert d.count == 5


def test_dirty_tracking():
    d = Dummy()
    d.count = 10
    assert d.dirty
    assert d.dirty_fields["count"] is True


def test_clear_dirty():
    d = Dummy()
    d.count = 20
    d.clear_dirty()
    assert not d.dirty


def test_status_property():
    d = Dummy()
    d.count = 42
    status = d.status
    assert status["dummy"]["count"]["value"] == 42


def test_to_dict():
    d = Dummy()
    d.count = 99
    result = d.to_dict()
    assert result["count"] == 99


def test_to_pydantic():
    d = Dummy()
    d.count = 88
    pyd = d.to_pydantic()
    assert pyd.count == 88


def test_sensitive_field_masking():
    d = SensitiveDummy()
    result = d.to_dict()
    assert result["secret"] == "***"


def test_include_in_dict_false():
    d = HiddenDummy()
    result = d.to_dict()
    assert "hidden" not in result


def test_type_inference_conflict_error():
    with pytest.raises(TypeError):
        class Conflict(StatusMixin):
            val: int = watch(default="not-an-int")
