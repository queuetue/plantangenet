from plantangenet.omni.mixins.omni import OmniMixin
from plantangenet.omni.helpers import watch, persist


class Dummy(OmniMixin):
    count: int = watch(default=0)
    notes: str = persist(default="initial")


def test_persisted_fields_registration():
    assert "count" in Dummy._omni_persisted_fields
    assert "notes" in Dummy._omni_persisted_fields
    assert "count" in Dummy._omni_observed_fields
    assert "notes" not in Dummy._omni_observed_fields


def test_default_values():
    d = Dummy()
    assert d.count == 0
    assert d.notes == "initial"


def test_dirty_tracking():
    d = Dummy()
    d.count = 42
    assert d.dirty
    d.clear_dirty()
    assert not d.dirty


def test_to_dict_includes_persisted():
    d = Dummy()
    d.count = 10
    d.notes = "hello"
    data = d.to_dict()
    assert data["count"] == 10
    assert data["notes"] == "hello"


def test_from_dict_hydrates():
    d = Dummy()
    d.from_dict({"count": 7, "notes": "restored"})
    assert d.count == 7
    assert d.notes == "restored"


def test_sensitive_masking():
    class Sensitive(OmniMixin):
        secret: str = watch(default="shh", sensitive=True)
    s = Sensitive()
    out = s.to_dict()
    assert out["secret"] == "***"


def test_include_in_dict_false():
    class Hidden(OmniMixin):
        hidden: int = watch(default=123, include_in_dict=False)
    h = Hidden()
    out = h.to_dict()
    assert "hidden" not in out
