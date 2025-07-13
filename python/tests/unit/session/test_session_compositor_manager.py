#!/usr/bin/env python3
# Copyright (c) 1998-2025 Scott Russell
# SPDX-License-Identifier: MIT

"""
Test suite for Session as compositor manager.
Tests the Session's ability to manage and coordinate different compositor types.
"""

from plantangenet.agents.agent import Agent
from plantangenet.compositor.graph_compositor import AgentSquad
from plantangenet.compositor.fb_types import ImmediateModeFBCompositor
from plantangenet.compositor.ml_types import ClassifierCompositor
from plantangenet.compositor.base import BaseCompositor
from plantangenet.policy.identity import Identity
from plantangenet.policy.policy import Policy
from plantangenet.session.session import Session
import pytest
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'python'))


class MockCompositor(BaseCompositor):
    """Mock compositor for testing."""

    def __init__(self, name: str = "mock"):
        super().__init__()
        self.name = name
        self.transform_calls = []
        self.compose_calls = []

    def transform(self, data, **kwargs):
        self.transform_calls.append((data, kwargs))
        return f"transformed_{data}_by_{self.name}"

    def compose(self, *args, **kwargs):
        self.compose_calls.append((args, kwargs))
        return f"composed_by_{self.name}"


class MockMLCompositor(ClassifierCompositor):
    """Mock ML compositor for testing."""

    def __init__(self):
        super().__init__()
        self.fitted = False

    def fit(self, X, y=None):
        self.fitted = True

    def predict(self, X):
        if isinstance(X, list):
            return [f"prediction_{i}" for i in range(len(X))]
        return ["prediction_0"]

    def update(self, X, y=None):
        pass


class MockAgent(Agent):
    """Mock agent for squad testing."""

    def __init__(self, name: str, **kwargs):
        super().__init__(**kwargs)
        self.agent_name = name  # Use agent_name to avoid name property conflict

    async def update(self) -> bool:
        return True

    @property
    def capabilities(self):
        return {"name": {self.agent_name}, "type": {"mock"}}


class TestSessionCompositorManager:
    """Test Session as compositor manager."""

    def setup_method(self):
        """Set up test fixtures."""
        self.identity = Identity(
            id="test_user", nickname="Test User", roles=[])
        self.policy = Policy(logger=None, namespace="test_policy")
        self.session = Session(
            id="test_session",
            policy=self.policy,
            identity=self.identity
        )

    def test_session_compositor_initialization(self):
        """Test that Session initializes compositor management correctly."""
        assert hasattr(self.session, 'compositors')
        assert hasattr(self.session, '_compositor_outputs')
        assert hasattr(self.session, '_shared_state')
        assert len(self.session.compositors) == 0
        assert len(self.session._compositor_outputs) == 0
        assert len(self.session._shared_state) == 0

    def test_add_remove_compositor(self):
        """Test adding and removing compositors."""
        mock_comp = MockCompositor("test_comp")

        # Test adding compositor
        self.session.add_compositor("mock", mock_comp)
        assert "mock" in self.session.compositors
        assert self.session.compositors["mock"] == mock_comp
        assert "mock" in self.session._compositor_outputs

        # Test removing compositor
        removed = self.session.remove_compositor("mock")
        assert removed == True
        assert "mock" not in self.session.compositors
        assert "mock" not in self.session._compositor_outputs

        # Test removing non-existent compositor
        removed = self.session.remove_compositor("nonexistent")
        assert removed == False

    def test_add_compositor_type_validation(self):
        """Test that only BaseCompositor instances can be added."""
        with pytest.raises(TypeError):
            self.session.add_compositor(
                "invalid", "not_a_compositor")  # type: ignore

        with pytest.raises(TypeError):
            self.session.add_compositor("invalid", 123)  # type: ignore

    def test_get_compositor_and_list(self):
        """Test getting and listing compositors."""
        mock_comp = MockCompositor("test_comp")
        ml_comp = MockMLCompositor()

        self.session.add_compositor("mock", mock_comp)
        self.session.add_compositor("ml", ml_comp)

        # Test getting specific compositor
        assert self.session.get_compositor("mock") == mock_comp
        assert self.session.get_compositor("ml") == ml_comp
        assert self.session.get_compositor("nonexistent") is None

        # Test listing compositors
        compositor_list = self.session.list_compositors()
        assert "mock" in compositor_list
        assert "ml" in compositor_list
        assert compositor_list["mock"] == "MockCompositor"
        assert compositor_list["ml"] == "MockMLCompositor"

    def test_transform_single_compositor(self):
        """Test transforming data with a single compositor."""
        mock_comp = MockCompositor("transformer")
        self.session.add_compositor("mock", mock_comp)

        result = self.session.transform_compositor(
            "mock", "test_data", extra_param="value")

        assert result == "transformed_test_data_by_transformer"
        assert len(mock_comp.transform_calls) == 1
        assert mock_comp.transform_calls[0] == (
            "test_data", {"extra_param": "value"})
        assert self.session.get_compositor_output("mock") == result

    def test_transform_nonexistent_compositor(self):
        """Test error handling for nonexistent compositor."""
        with pytest.raises(KeyError, match="Compositor 'nonexistent' not found"):
            self.session.transform_compositor("nonexistent", "data")

    def test_transform_all_compositors(self):
        """Test transforming data with all compositors."""
        mock1 = MockCompositor("comp1")
        mock2 = MockCompositor("comp2")

        self.session.add_compositor("c1", mock1)
        self.session.add_compositor("c2", mock2)

        data_map = {
            "c1": "data_for_c1",
            "c2": "data_for_c2"
        }

        results = self.session.transform_all_compositors(data_map)

        assert "c1" in results
        assert "c2" in results
        assert results["c1"] == "transformed_data_for_c1_by_comp1"
        assert results["c2"] == "transformed_data_for_c2_by_comp2"

        # Verify outputs are cached
        assert self.session.get_compositor_output("c1") == results["c1"]
        assert self.session.get_compositor_output("c2") == results["c2"]

    def test_compose_single_compositor(self):
        """Test composing output from a single compositor."""
        mock_comp = MockCompositor("composer")
        self.session.add_compositor("mock", mock_comp)

        result = self.session.compose_compositor(
            "mock", "arg1", "arg2", kwarg="value")

        assert result == "composed_by_composer"
        assert len(mock_comp.compose_calls) == 1
        assert mock_comp.compose_calls[0] == (
            ("arg1", "arg2"), {"kwarg": "value"})
        assert self.session.get_compositor_output("mock") == result

    def test_compose_all_compositors(self):
        """Test composing outputs from all compositors."""
        mock1 = MockCompositor("comp1")
        mock2 = MockCompositor("comp2")

        self.session.add_compositor("c1", mock1)
        self.session.add_compositor("c2", mock2)

        results = self.session.compose_all_compositors(global_param="test")

        assert "c1" in results
        assert "c2" in results
        assert results["c1"] == "composed_by_comp1"
        assert results["c2"] == "composed_by_comp2"

        # Verify compose was called with kwargs
        assert mock1.compose_calls[0][1] == {"global_param": "test"}
        assert mock2.compose_calls[0][1] == {"global_param": "test"}

    def test_shared_state_management(self):
        """Test shared state management across compositors."""
        # Test setting and getting individual keys
        self.session.set_shared_state("key1", "value1")
        self.session.set_shared_state("key2", {"nested": "value"})

        assert self.session.get_shared_state("key1") == "value1"
        assert self.session.get_shared_state("key2") == {"nested": "value"}
        assert self.session.get_shared_state("nonexistent") is None

        # Test getting all shared state
        all_state = self.session.get_shared_state()
        assert all_state == {"key1": "value1", "key2": {"nested": "value"}}

        # Test clearing shared state
        self.session.clear_shared_state()
        assert self.session.get_shared_state() == {}

    def test_broadcast_to_compositors(self):
        """Test broadcasting data to multiple compositors."""
        mock1 = MockCompositor("comp1")
        mock2 = MockCompositor("comp2")
        mock3 = MockCompositor("comp3")

        self.session.add_compositor("c1", mock1)
        self.session.add_compositor("c2", mock2)
        self.session.add_compositor("c3", mock3)

        # Test broadcasting to all compositors
        results = self.session.broadcast_to_compositors("broadcast_data")

        assert len(results) == 3
        assert results["c1"] == "transformed_broadcast_data_by_comp1"
        assert results["c2"] == "transformed_broadcast_data_by_comp2"
        assert results["c3"] == "transformed_broadcast_data_by_comp3"

        # Test broadcasting to filtered compositors
        filtered_results = self.session.broadcast_to_compositors(
            "filtered_data",
            compositor_filter=["c1", "c3"]
        )

        assert len(filtered_results) == 2
        assert "c1" in filtered_results
        assert "c3" in filtered_results
        assert "c2" not in filtered_results

    def test_real_compositor_integration(self):
        """Test integration with real compositor types."""
        # Add different types of real compositors
        ml_comp = MockMLCompositor()
        fb_comp = ImmediateModeFBCompositor(width=100, height=100)
        squad = AgentSquad(name="test_squad")

        self.session.add_compositor("ml", ml_comp)
        self.session.add_compositor("ui", fb_comp)
        self.session.add_compositor("squad", squad)

        # Test that all compositor types are properly managed
        compositor_types = self.session.list_compositors()
        assert "ml" in compositor_types
        assert "ui" in compositor_types
        assert "squad" in compositor_types

        # Test squad as core compositor
        agent = MockAgent("test_agent", namespace="test", logger=None)
        graph_data = {
            "nodes": {"agent1": agent},
            "edges": {"agent1": []}
        }

        squad_result = self.session.transform_compositor("squad", graph_data)
        assert isinstance(squad_result, dict)
        assert "nodes" in squad_result

        # Test ML compositor
        ml_comp.compose(["training_data"])  # Fit the model
        ml_result = self.session.transform_compositor("ml", ["test_data"])
        assert isinstance(ml_result, list)

        # Test UI compositor
        ui_events = [{"type": "button_click", "id": "test_button"}]
        ui_result = self.session.transform_compositor("ui", ui_events)
        assert isinstance(ui_result, dict)
        assert "framebuffer" in ui_result

    def test_persisted_state_includes_compositors(self):
        """Test that persisted state includes compositor information."""
        mock_comp = MockCompositor("test")
        self.session.add_compositor("mock", mock_comp)

        state = self.session.persisted_state()

        assert "compositor_count" in state
        assert "active_compositors" in state
        assert state["compositor_count"] == 1
        assert state["active_compositors"] == ["mock"]


if __name__ == "__main__":
    # Run tests manually if executed directly
    import unittest

    class TestRunner:
        def __init__(self):
            self.test_class = TestSessionCompositorManager()

        def run_all_tests(self):
            """Run all test methods."""
            test_methods = [method for method in dir(self.test_class)
                            if method.startswith('test_')]

            passed = 0
            failed = 0

            for method_name in test_methods:
                print(f"\n🧪 Running {method_name}...")
                try:
                    # Set up fresh test environment
                    self.test_class.setup_method()

                    # Run the test
                    method = getattr(self.test_class, method_name)
                    method()

                    print(f"  ✅ PASSED")
                    passed += 1

                except Exception as e:
                    print(f"  ❌ FAILED: {e}")
                    failed += 1

            print(f"\n📊 Test Results: {passed} passed, {failed} failed")
            return failed == 0

    print("🚀 Running Session Compositor Manager Tests")
    runner = TestRunner()
    success = runner.run_all_tests()

    if success:
        print("\n✅ All tests passed!")
        exit(0)
    else:
        print("\n❌ Some tests failed!")
        exit(1)
