#!/usr/bin/env python3
# Copyright (c) 1998-2025 Scott Russell
# SPDX-License-Identifier: MIT

"""
Demo of Unified Compositor/Squad Architecture

This demonstrates the concept where a 'composition' is the squad graph itself.
Shows how Squad can be a specialized Compositor for Agent objects.
"""

import time
import json
from plantangenet.logger import Logger
from plantangenet.policy.policy import Policy
from plantangenet.policy.identity import Identity
from plantangenet.agents.agent import Agent
from plantangenet.compositor.graph_compositor import (
    AgentSquad,
    AgentFilterRule,
    CommunicationFlowRule,
    SessionAnalysisRule
)
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'python'))


class DemoAgent(Agent):
    """Simple demo agent for testing graph composition."""

    def __init__(self, agent_type: str = "demo", **kwargs):
        super().__init__(**kwargs)
        self.agent_type = agent_type
        self._message_count = 0

    async def update(self) -> bool:
        # Simulate some activity
        self._message_count += 1
        return True

    @property
    def capabilities(self):
        return {
            "message_types": ["demo.ping", "demo.pong"],
            "can_coordinate": True,
            "agent_type": self.agent_type
        }

    def send_message_to(self, other_agent):
        """Simulate sending a message to another agent."""
        self._message_count += 1
        print(
            f"  📤 {self.name} -> {other_agent.name}: message #{self._message_count}")


def create_demo_agents():
    """Create a variety of demo agents for testing."""
    logger = Logger()

    agents = {
        "coordinator": DemoAgent(agent_type="coordinator", namespace="demo", logger=logger),
        "worker1": DemoAgent(agent_type="worker", namespace="demo", logger=logger),
        "worker2": DemoAgent(agent_type="worker", namespace="demo", logger=logger),
        "monitor": DemoAgent(agent_type="monitor", namespace="demo", logger=logger),
        "analyzer": DemoAgent(agent_type="analyzer", namespace="demo", logger=logger)
    }

    return agents


def demonstrate_basic_graph_composition():
    """Demonstrate basic graph composition with agents."""
    print("\n🔧 === BASIC GRAPH COMPOSITION ===")

    # Create squad as graph compositor
    squad = AgentSquad(name="demo_squad")
    agents = create_demo_agents()

    # Add agents as nodes in the graph
    print("\n📋 Adding agents to squad graph:")
    for name, agent in agents.items():
        squad.add_node(name, agent, {"role": name})
        print(f"  ✅ Added {name} (type: {agent.agent_type})")

    # Create relationships between agents
    print("\n🔗 Creating agent relationships:")
    relationships = [
        ("coordinator", "worker1", "supervision"),
        ("coordinator", "worker2", "supervision"),
        ("monitor", "coordinator", "oversight"),
        ("monitor", "worker1", "monitoring"),
        ("monitor", "worker2", "monitoring"),
        ("analyzer", "monitor", "data_analysis"),
        ("worker1", "worker2", "peer_communication")
    ]

    for from_agent, to_agent, edge_type in relationships:
        squad.add_edge(from_agent, to_agent, edge_type)
        print(f"  🔗 {from_agent} --{edge_type}--> {to_agent}")

    # Get the graph composition
    print("\n📊 Graph Composition:")
    composition = squad.compose_graph()

    print(f"  Squad: {composition['squad_name']}")
    print(f"  Nodes: {composition['graph_properties']['node_count']}")
    print(f"  Edges: {composition['graph_properties']['edge_count']}")
    print(f"  Density: {composition['graph_properties']['density']:.3f}")
    print(
        f"  Components: {len(composition['graph_properties']['connected_components'])}")
    print(f"  Hubs: {composition['graph_properties']['communication_hubs']}")

    return squad, agents


def demonstrate_composition_rules():
    """Demonstrate how composition rules transform graph representations."""
    print("\n🔄 === COMPOSITION RULES ===")

    squad, agents = demonstrate_basic_graph_composition()

    # Add composition rules
    print("\n🔧 Adding composition rules:")

    # Rule 1: Filter only worker agents
    worker_filter = AgentFilterRule(
        lambda node: node.get("agent_type") == "worker")
    squad.add_composition_rule(worker_filter)
    print("  ✅ Added worker filter rule")

    # Rule 2: Add communication flow analysis
    comm_analysis = CommunicationFlowRule()
    squad.add_composition_rule(comm_analysis)
    print("  ✅ Added communication flow analysis rule")

    # Get transformed composition
    print("\n📊 Transformed Composition (workers only):")
    composition = squad.compose_graph()

    print(f"  Filtered nodes: {len(composition['nodes'])}")
    for node_id, node_data in composition['nodes'].items():
        print(f"    {node_id}: {node_data['agent_type']}")

    if "communication_analysis" in composition:
        comm_data = composition["communication_analysis"]
        print(
            f"  Communication density: {comm_data['communication_density']:.3f}")
        print(f"  Most connected: {comm_data['most_connected_nodes']}")

    return squad


def demonstrate_session_integration():
    """Demonstrate integration with sessions."""
    print("\n👥 === SESSION INTEGRATION ===")

    squad = AgentSquad(name="session_demo_squad")
    agents = create_demo_agents()

    # Create identities and sessions
    identities = {
        "admin": Identity(id="admin_1", nickname="Admin User", roles=[]),
        "user": Identity(id="user_1", nickname="Regular User", roles=[])
    }

    print("\n🆔 Creating sessions:")
    sessions = {}
    for name, identity in identities.items():
        session = squad.create_session(identity)
        sessions[name] = session
        print(
            f"  ✅ Created session for {identity.nickname} (ID: {session._id[:8]})")

    # Add agents to sessions
    print("\n🔗 Adding agents to sessions:")
    squad.add_agent_to_session(agents["coordinator"], sessions["admin"])
    squad.add_agent_to_session(agents["monitor"], sessions["admin"])
    squad.add_agent_to_session(agents["worker1"], sessions["user"])
    squad.add_agent_to_session(agents["worker2"], sessions["user"])
    squad.add_agent_to_session(agents["analyzer"], sessions["user"])

    print("  👑 Admin session: coordinator, monitor")
    print("  👤 User session: worker1, worker2, analyzer")

    # Add session analysis rule
    squad.add_composition_rule(SessionAnalysisRule())

    # Get composition with session analysis
    print("\n📊 Session-aware composition:")
    composition = squad.compose_graph()

    if "session_analysis" in composition:
        session_data = composition["session_analysis"]
        print(f"  Sessions: {session_data['session_count']}")
        print(f"  Agents: {session_data['agent_count']}")
        print(
            f"  Session-agent connections: {session_data['session_agent_connections']}")
        print(
            f"  Avg agents per session: {session_data['average_agents_per_session']:.1f}")

    return squad, sessions


def demonstrate_dynamic_graph_evolution():
    """Demonstrate how the graph evolves dynamically."""
    print("\n🔄 === DYNAMIC GRAPH EVOLUTION ===")

    squad, sessions = demonstrate_session_integration()

    print("\n⏰ Simulating agent activity...")

    # Simulate some agent interactions
    agents = {name: squad.nodes[name]
              for name in squad.nodes if name.startswith("agent_")}

    # Track compositions over time
    compositions = []
    for i in range(3):
        print(f"\n  📸 Snapshot {i+1}:")

        # Simulate message exchanges
        if len(agents) >= 2:
            agent_list = list(agents.values())
            agent_list[0].send_message_to(agent_list[1])
            if len(agent_list) > 2:
                agent_list[1].send_message_to(agent_list[2])

        # Get current composition
        composition = squad.compose_graph()
        compositions.append(composition)

        # Show current state
        if "communication_analysis" in composition:
            comm_data = composition["communication_analysis"]
            print(
                f"    Communication density: {comm_data['communication_density']:.3f}")
            print(f"    Total connections: {comm_data['total_connections']}")

        time.sleep(0.1)  # Brief pause

    print("\n📈 Graph evolution complete")
    return compositions


def demonstrate_subgraph_extraction():
    """Demonstrate extracting subgraphs."""
    print("\n🧩 === SUBGRAPH EXTRACTION ===")

    squad, _ = demonstrate_basic_graph_composition()

    # Extract subgraph of just workers and their coordinator
    worker_nodes = ["coordinator", "worker1", "worker2"]
    subgraph = squad.get_subgraph(worker_nodes)

    print(f"\n🔍 Worker subgraph:")
    print(f"  Nodes: {len(subgraph['nodes'])}")
    print(
        f"  Edges: {sum(len(targets) for targets in subgraph['edges'].values())}")

    for node_id in subgraph['nodes']:
        connections = subgraph['edges'].get(node_id, [])
        print(f"    {node_id} -> {connections}")

    return subgraph


def print_detailed_composition(composition: dict):
    """Pretty print a detailed composition."""
    print("\n📋 === DETAILED COMPOSITION ===")
    print(json.dumps({
        "squad_name": composition["squad_name"],
        "timestamp": composition["timestamp"],
        "node_count": len(composition["nodes"]),
        "edge_count": sum(len(targets) for targets in composition["edges"].values()),
        "graph_properties": composition["graph_properties"],
        "nodes": {k: {
            "type": v.get("agent_type", v.get("object_type")),
            "name": v.get("agent_name", "unnamed")
        } for k, v in composition["nodes"].items()},
        "communication_analysis": composition.get("communication_analysis", {}),
        "session_analysis": composition.get("session_analysis", {})
    }, indent=2))


def main():
    """Run all demonstrations."""
    print("🚀 === UNIFIED COMPOSITOR/SQUAD ARCHITECTURE DEMO ===")
    print("Demonstrating: 'A composition is the squad graph'")

    try:
        # Basic graph composition
        squad, agents = demonstrate_basic_graph_composition()

        # Composition rules
        squad_with_rules = demonstrate_composition_rules()

        # Session integration
        squad_with_sessions, sessions = demonstrate_session_integration()

        # Dynamic evolution
        compositions = demonstrate_dynamic_graph_evolution()

        # Subgraph extraction
        subgraph = demonstrate_subgraph_extraction()

        # Show final detailed composition
        final_composition = squad_with_sessions.compose_graph()
        print_detailed_composition(final_composition)

        print("\n✅ === DEMO COMPLETE ===")
        print("Key insights:")
        print("  • Squad IS a graph compositor for agents")
        print("  • The 'composition' is the living graph of relationships")
        print("  • Composition rules transform graph representations")
        print("  • Sessions integrate naturally as special graph nodes")
        print("  • Graph evolves dynamically as agents interact")
        print("  • Subgraphs can be extracted for analysis")

    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
