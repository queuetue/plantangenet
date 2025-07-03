#!/usr/bin/env python3
"""
Test script for the Vanilla policy implementation.
"""

from plantangenet.policy.vanilla import Vanilla
from plantangenet.policy.evaluator import EvaluationResult
from plantangenet.policy.base import Identity, Role, Statement
import asyncio
import logging
import sys
import os
import pytest

# Add the python directory to the path
sys.path.insert(0, '/home/srussell/Development/groovebox/python')

# Direct imports to avoid package import issues

logging.basicConfig(level=logging.INFO)


def test_vanilla_policy():
    """Test the Vanilla policy implementation."""

    print("Creating Vanilla policy instance...")
    policy = Vanilla(logger=logging.getLogger(
        "vanilla_test"), namespace="test")

    print("Setting up policy...")
    policy.setup()

    print("Creating test identity...")
    identity = Identity(identity_id="user123", name="Test User")
    identity_id = policy.add_identity(identity)
    print(f"Added identity: {identity_id}")

    print("Creating test role...")
    role = Role(role_id="role456", name="admin",
                description="Administrator role")
    role_name = policy.add_role(role)
    print(f"Added role: {role_name}")

    print("Adding identity to role...")
    policy.add_identity_to_role(identity, role)
    print(f"Added identity to role")

    print("Checking if identity has role...")
    has_role = policy.has_role("user123", "admin")
    print(f"Identity has admin role: {has_role}")

    print("Getting role...")
    retrieved_role = policy.get_role("admin")
    print(f"Retrieved role: {retrieved_role}")

    print("Checking includes_any_role...")
    includes_admin = policy.includes_any_role(["admin", "user"])
    print(f"Includes admin or user role: {includes_admin}")

    print("Adding policy statement...")
    statement_id = policy.add_statement(
        roles=["admin"],
        effect="allow",
        action="read",
        resource="database"
    )
    print(f"Added statement: {statement_id}")

    print("Getting identity...")
    retrieved_identity = policy.get_identity("user123")
    print(f"Retrieved identity: {retrieved_identity}")

    print("Testing evaluate method...")
    result = policy.evaluate(identity, "read", "database")
    print(
        f"Evaluation result: passed={result.passed}, reason='{result.reason}'")

    print("Cleaning up...")
    policy.teardown()
    print("Policy teardown completed")
    print("\n✅ All tests completed successfully!")


if __name__ == "__main__":
    asyncio.run(test_vanilla_policy())
