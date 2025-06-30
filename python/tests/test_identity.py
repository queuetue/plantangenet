from plantangenet.policy.identity import Identity


def test_identity_creation_defaults():
    identity = Identity(id="u1", nickname="User One")
    assert identity.id == "u1"
    assert identity.nickname == "User One"
    assert identity.roles == []
    assert isinstance(identity.dict(), dict)
