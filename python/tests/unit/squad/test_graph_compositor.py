#!/usr/bin/env python3
# Copyright (c) 1998-2025 Scott Russell
# SPDX-License-Identifier: MIT

"""
Test suite for the unified Compositor/Squad architecture.
"""

from plantangenet.logger import Logger
from plantangenet.policy.identity import Identity
from plantangenet.agents.agent import Agent
from plantangenet.compositor.graph_compositor import (
    AgentSquad,
    AgentFilterRule,
    CommunicationFlowRule,
    SessionAnalysisRule
)
import pytest
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'python'))


class MyAgent(Agent):
    """Test agent for unit tests."""

    def __init__(self, agent_type: str = "test", **kwargs):
        super().__init__(**kwargs)
        self.agent_type = agent_type

    async def update(self) -> bool:
        return True

    @property
    def capabilities(self):
        return {
            "agent_type": self.agent_type,
            "test_capability": True
        }


class UnifiedCompositorSquad:
    """Test cases for the unified Compositor/Squad architecture."""

    def setup_method(self):
        """Set up test fixtures."""
        self.logger = Logger()
        self.squad = AgentSquad(name="test_squad")

        # Create test agents
        self.agents = {
            "agent1": MyAgent(agent_type="worker", namespace="test", logger=self.logger),
            "agent2": MyAgent(agent_type="worker", namespace="test", logger=self.logger),
            "agent3": MyAgent(agent_type="coordinator", namespace="test", logger=self.logger)
        }

    def test_agent_squad_is_graph_compositor(self):
        """Test that AgentSquad works as a graph compositor."""
        # Add agents as nodes
        for name, agent in self.agents.items():
            self.squad.add_node(name, agent)

        # Verify nodes were added
        assert len(self.squad.nodes) == 3
        assert "agent1" in self.squad.nodes
        assert isinstance(self.squad.nodes["agent1"], Agent)

    def test_graph_edges_and_relationships(self):
        """Test adding edges between agents."""
        # Add agents
        for name, agent in self.agents.items():
            self.squad.add_node(name, agent)

        # Add relationships
        self.squad.add_edge("agent3", "agent1", "supervision")
        self.squad.add_edge("agent3", "agent2", "supervision")
        self.squad.add_edge("agent1", "agent2", "peer_communication")

        # Verify edges
        assert "agent1" in self.squad.get_neighbors("agent3")
        assert "agent2" in self.squad.get_neighbors("agent3")
        assert "agent2" in self.squad.get_neighbors("agent1")

    def test_graph_composition_generation(self):
        """Test that compose_graph generates proper composition."""
        # Set up graph
        for name, agent in self.agents.items():
            self.squad.add_node(name, agent)

        self.squad.add_edge("agent3", "agent1", "supervision")

        # Get composition
        composition = self.squad.compose_graph()

        # Verify composition structure
        assert "squad_name" in composition
        assert "nodes" in composition
        assert "edges" in composition
        assert "graph_properties" in composition

        # Verify graph properties
        props = composition["graph_properties"]
        assert props["node_count"] == 3
        assert props["edge_count"] == 1
        assert isinstance(props["density"], float)
        assert isinstance(props["connected_components"], list)

    def test_composition_rules_transform_graph(self):
        """Test that composition rules transform the graph representation."""
        # Set up graph
        for name, agent in self.agents.items():
            self.squad.add_node(name, agent)

        # Add filter rule for workers only - check capabilities field
        worker_filter = AgentFilterRule(
            lambda node: node.get("capabilities", {}).get(
                "agent_type") == "worker"
        )
        self.squad.add_composition_rule(worker_filter)

        # Get composition
        composition = self.squad.compose_graph()

        # Should only have worker nodes after filtering
        assert len(composition["nodes"]) == 2
        for node_id, node_data in composition["nodes"].items():
            capabilities = node_data.get("capabilities", {})
            assert capabilities.get("agent_type") == "worker"

    def test_session_integration_as_graph_nodes(self):
        """Test that sessions integrate as special graph nodes."""
        # Create identity and session
        identity = Identity(id="test_user", nickname="Test User", roles=[])
        session = self.squad.create_session(identity)

        # Session should be added as a node
        session_node_id = f"session_{session._id}"
        assert session_node_id in self.squad.nodes
        assert self.squad.nodes[session_node_id] == session

        # Add agent to session
        agent = self.agents["agent1"]
        self.squad.add_agent_to_session(agent, session)

        # Should create edge from session to agent
        agent_node_id = f"agent_{agent.id}"
        assert agent_node_id in self.squad.get_neighbors(session_node_id)

    def test_subgraph_extraction(self):
        """Test extracting subgraphs from the main graph."""
        # Set up graph
        for name, agent in self.agents.items():
            self.squad.add_node(name, agent)

        self.squad.add_edge("agent3", "agent1", "supervision")
        self.squad.add_edge("agent1", "agent2", "peer_communication")

        # Extract subgraph with just agent1 and agent2
        subgraph = self.squad.get_subgraph(["agent1", "agent2"])

        # Verify subgraph
        assert len(subgraph["nodes"]) == 2
        assert "agent1" in subgraph["nodes"]
        assert "agent2" in subgraph["nodes"]
        assert "agent3" not in subgraph["nodes"]

        # Verify edges within subgraph
        assert "agent2" in subgraph["edges"].get("agent1", [])

    def test_dynamic_graph_modification(self):
        """Test adding and removing nodes dynamically."""
        # Add initial agents
        self.squad.add_node("agent1", self.agents["agent1"])
        self.squad.add_node("agent2", self.agents["agent2"])
        self.squad.add_edge("agent1", "agent2", "communication")

        # Verify initial state
        assert len(self.squad.nodes) == 2
        assert "agent2" in self.squad.get_neighbors("agent1")

        # Remove agent2
        self.squad.remove_node("agent2")

        # Verify removal
        assert len(self.squad.nodes) == 1
        assert "agent2" not in self.squad.nodes
        assert "agent2" not in self.squad.get_neighbors("agent1")

    def test_communication_flow_analysis(self):
        """Test communication flow analysis composition rule."""
        # Set up graph with multiple connections
        for name, agent in self.agents.items():
            self.squad.add_node(name, agent)

        self.squad.add_edge("agent3", "agent1", "communication")
        self.squad.add_edge("agent3", "agent2", "communication")
        self.squad.add_edge("agent1", "agent2", "communication")

        # Add communication analysis rule
        self.squad.add_composition_rule(CommunicationFlowRule())

        # Get composition
        composition = self.squad.compose_graph()

        # Verify communication analysis was added
        assert "communication_analysis" in composition
        comm_data = composition["communication_analysis"]
        assert "total_connections" in comm_data
        assert "communication_density" in comm_data
        assert "most_connected_nodes" in comm_data

        # Verify metrics make sense
        assert comm_data["total_connections"] == 3
        assert comm_data["communication_density"] > 0

    def test_graph_properties_calculation(self):
        """Test calculation of graph properties."""
        # Create a more complex graph
        for name, agent in self.agents.items():
            self.squad.add_node(name, agent)

        # Create hub pattern (agent3 connected to others)
        self.squad.add_edge("agent3", "agent1", "supervision")
        self.squad.add_edge("agent3", "agent2", "supervision")

        composition = self.squad.compose_graph()
        props = composition["graph_properties"]

        # Verify basic properties
        assert props["node_count"] == 3
        assert props["edge_count"] == 2

        # agent3 should be identified as a hub
        assert "agent3" in props["communication_hubs"]

        # Should have one connected component
        assert len(props["connected_components"]) == 1
        assert len(props["connected_components"][0]) == 3

    def test_error_handling_invalid_operations(self):
        """Test error handling for invalid graph operations."""
        self.squad.add_node("agent1", self.agents["agent1"])
        # Adding duplicate node should overwrite (current impl), but adding edge to non-existent node should fail
        with pytest.raises(ValueError):
            self.squad.add_edge("agent1", "nonexistent", "invalid")
        with pytest.raises(ValueError):
            self.squad.add_edge("nonexistent", "agent1", "invalid")

    def test_dynamic_rule_addition_removal(self):
        """Test adding and removing rules at runtime."""
        for name, agent in self.agents.items():
            self.squad.add_node(name, agent)
        # Add a filter rule
        worker_filter = AgentFilterRule(lambda node: node.get(
            "capabilities", {}).get("agent_type") == "worker")
        self.squad.add_composition_rule(worker_filter)
        composition = self.squad.compose_graph()
        assert len(composition["nodes"]) == 2
        # Remove the rule and check all nodes are present again
        self.squad.composition_rules.clear()
        composition = self.squad.compose_graph()
        assert len(composition["nodes"]) == 3

    def test_mlcompositor_stub(self):
        """Test that MLCompositor raises NotImplementedError for abstract methods."""
        from plantangenet.compositor.ml_types import MLCompositor

        # MLCompositor is abstract, so we need a concrete implementation to test
        class TestMLCompositor(MLCompositor):
            def fit(self, X, y=None): pass
            def predict(self, X): raise NotImplementedError(
                "predict not implemented")

            def update(self, X, y=None): pass

        mlc = TestMLCompositor()
        with pytest.raises(NotImplementedError):
            # Should call predict() which raises NotImplementedError
            mlc.transform([1, 2, 3])

    def test_subgraph_extraction_disconnected(self):
        """Test subgraph extraction with disconnected nodes."""
        self.squad.add_node("agent1", self.agents["agent1"])
        self.squad.add_node("agent2", self.agents["agent2"])
        self.squad.add_node("agent3", self.agents["agent3"])
        # Only connect agent1 and agent2
        self.squad.add_edge("agent1", "agent2", "peer")
        subgraph = self.squad.get_subgraph(["agent3"])
        assert len(subgraph["nodes"]) == 1
        assert "agent3" in subgraph["nodes"]
        assert subgraph["edges"]["agent3"] == []

    def test_metadata_update_after_node_creation(self):
        """Test updating node metadata after creation."""
        self.squad.add_node("agent1", self.agents["agent1"])
        # Update metadata
        self.squad.graph_metadata["node_agent1"]["custom"] = "updated"
        assert self.squad.graph_metadata["node_agent1"]["custom"] == "updated"

    def test_graph_transform_method(self):
        """Test the unified transform method for graph operations."""
        # Add initial nodes
        self.squad.add_node("agent1", self.agents["agent1"])

        # Test transform with graph data
        graph_data = {
            "nodes": {"agent2": self.agents["agent2"]},
            "edges": {"agent1": ["agent2"]}
        }

        result = self.squad.transform(graph_data)

        # Should have merged the data and returned composition
        assert "agent2" in self.squad.nodes
        assert "agent2" in self.squad.get_neighbors("agent1")
        assert isinstance(result, dict)
        assert "nodes" in result
        assert "edges" in result


if __name__ == "__main__":
    # Run tests manually if executed directly
    import unittest

    class TestRunner:
        def __init__(self):
            self.test_class = UnifiedCompositorSquad()

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

    print("🚀 Running Unified Compositor/Squad Architecture Tests")
    runner = TestRunner()
    success = runner.run_all_tests()

    if success:
        print("\n✅ All tests passed!")
        exit(0)
    else:
        print("\n❌ Some tests failed!")
        exit(1)
