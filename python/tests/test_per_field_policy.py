# Copyright (c) 1998-2025 Scott Russell
# SPDX-License-Identifier: MIT

import pytest
import asyncio
from plantangenet.policy.vanilla import Vanilla
from plantangenet.policy.base import Identity, Role, Statement
from plantangenet.omni.observable import Observable
from plantangenet.omni.persisted import PersistedBase
from plantangenet.omni.omni import Omni


class MockSession:
    def __init__(self, identity: str):
        self.identity = identity


class ModelTest(Omni):
    """Test model with both Observable and PersistedBase fields."""

    # Observable field with policy enforcement
    name = Observable(field_type=str, default="")

    # PersistedBase field with policy enforcement
    secret = PersistedBase(default="")

    def __init__(self, session=None, policy=None):
        super().__init__()
        self.session = session
        self.policy = policy


class TestPerFieldPolicy:

    @pytest.fixture
    def policy(self):
        """Create a policy with test data."""
        policy = Vanilla(logger=None, namespace="test")

        # Create identities
        admin_identity = Identity(identity_id="admin", name="Admin User")
        user_identity = Identity(identity_id="user", name="Regular User")

        policy.add_identity(admin_identity)
        policy.add_identity(user_identity)

        # Create roles
        admin_role = Role(role_id="admin_role", name="admin",
                          description="Administrator role")
        user_role = Role(role_id="user_role", name="user",
                         description="Regular user role")

        policy.add_role(admin_role)
        policy.add_role(user_role)

        # Link identities to roles
        policy.add_identity_to_role(admin_identity, admin_role)
        policy.add_identity_to_role(user_identity, user_role)

        # Add statements - admin can read/write everything, user can only read
        policy.add_statement(
            roles=["admin"],
            effect="allow",
            action=["read"],
            resource=["*"]
        )
        policy.add_statement(
            roles=["admin"],
            effect="allow",
            action=["write"],
            resource=["*"]
        )
        policy.add_statement(
            roles=["user"],
            effect="allow",
            action=["read"],
            resource=["*"]
        )
        policy.add_statement(
            roles=["user"],
            effect="deny",
            action=["write"],
            resource=["*"]
        )

        return policy

    def test_observable_field_access_allowed(self, policy):
        """Test that Observable field access works when policy allows it."""
        admin_session = MockSession("admin")
        model = ModelTest(session=admin_session, policy=policy)

        # Admin should be able to read and write
        model.name = "test_name"  # Should not raise
        assert model.name == "test_name"

    def test_observable_field_access_denied(self, policy):
        """Test that Observable field access is denied when policy denies it."""
        # Start with admin to set initial value
        admin_session = MockSession("admin")
        model = ModelTest(session=admin_session, policy=policy)

        # Admin sets initial value
        model.name = "initial"

        # Now switch to user session
        user_session = MockSession("user")
        model.session = user_session

        # User can read
        assert model.name == "initial"  # Should not raise

        # User cannot write
        with pytest.raises(PermissionError, match="Access denied: write operation"):
            model.name = "hacked"

    def test_persisted_field_access_allowed(self, policy):
        """Test that PersistedBase field access works when policy allows it."""
        admin_session = MockSession("admin")
        model = ModelTest(session=admin_session, policy=policy)

        # Admin should be able to read and write
        model.secret = "top_secret"  # Should not raise
        assert model.secret == "top_secret"

    def test_persisted_field_access_denied(self, policy):
        """Test that PersistedBase field access is denied when policy denies it."""
        # Start with admin to set initial value
        admin_session = MockSession("admin")
        model = ModelTest(session=admin_session, policy=policy)

        # Admin sets initial value
        model.secret = "initial_secret"

        # Now switch to user session
        user_session = MockSession("user")
        model.session = user_session

        # User can read
        assert model.secret == "initial_secret"  # Should not raise

        # User cannot write
        with pytest.raises(PermissionError, match="Access denied: write operation"):
            model.secret = "stolen_secret"

    def test_no_policy_no_enforcement(self):
        """Test that fields work normally when no policy is set."""
        session = MockSession("anyone")
        model = ModelTest(session=session, policy=None)  # No policy

        # Should work without any policy checks
        model.name = "no_policy"
        assert model.name == "no_policy"

        model.secret = "no_policy_secret"
        assert model.secret == "no_policy_secret"

    def test_no_session_no_enforcement(self, policy):
        """Test that fields work normally when no session is set."""
        model = ModelTest(session=None, policy=policy)  # No session

        # Should work without any policy checks
        model.name = "no_session"
        assert model.name == "no_session"

        model.secret = "no_session_secret"
        assert model.secret == "no_session_secret"


if __name__ == "__main__":
    pytest.main([__file__])
