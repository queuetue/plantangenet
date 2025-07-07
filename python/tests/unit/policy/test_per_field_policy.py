import pytest
from plantangenet.policy import Policy
from plantangenet.policy.policy import Identity, Role, Statement
from plantangenet.omni.observable import Observable
from plantangenet.omni.persisted import PersistedBase
from plantangenet.omni import Omni


class MockSession:
    def __init__(self, identity):
        self.identity = identity


class ModelTest(Omni):
    """Test model with both Observable and PersistedBase fields."""
    name = Observable(field_type=str, default="")
    secret = PersistedBase(default="")


class TestPerFieldPolicy:
    @pytest.fixture
    def policy(self):
        policy = Policy(logger=None, namespace="test")
        admin_identity = Identity(
            id="admin", nickname="Admin User", metadata={}, roles=["admin"])
        user_identity = Identity(
            id="user", nickname="Regular User", metadata={}, roles=["user"])
        policy.add_identity(admin_identity)
        policy.add_identity(user_identity)
        admin_role = Role(id="admin_role", name="admin",
                          description="Administrator role", members=[])
        user_role = Role(id="user_role", name="user",
                         description="Regular user role", members=[])
        policy.add_role(admin_role)
        policy.add_role(user_role)
        policy.add_identity_to_role(admin_identity, admin_role)
        policy.add_identity_to_role(user_identity, user_role)
        policy.add_statement(["admin_role"], "allow", ["read", "write"], ["*"])
        policy.add_statement(["user_role"], "allow", ["read"], ["*"])
        return policy

    def test_admin_can_write(self, policy):
        admin_identity = policy.get_identity("admin")
        session = MockSession(identity=admin_identity)
        model = ModelTest(session=session, policy=policy)
        model.name = "new name"
        model.secret = "top secret"
        assert model.name == "new name"
        assert model.secret == "top secret"

    def test_user_can_read_but_not_write(self, policy):
        user_identity = policy.get_identity("user")
        session = MockSession(identity=user_identity)
        model = ModelTest(session=session, policy=policy)
        # User can read
        _ = model.name
        _ = model.secret
        # User cannot write
        with pytest.raises(PermissionError):
            model.name = "should fail"
        with pytest.raises(PermissionError):
            model.secret = "should fail"
