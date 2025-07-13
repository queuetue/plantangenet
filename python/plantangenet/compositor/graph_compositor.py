# Copyright (c) 1998-2025 Scott Russell
# SPDX-License-Identifier: MIT

"""
Prototype implementation of unified Compositor/Squad architecture.

This demonstrates the concept where a 'composition' is the squad graph itself.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Callable
import time
import uuid
from plantangenet.agents.agent import Agent
from plantangenet.session.session import Session
from plantangenet.policy.policy import Policy
from plantangenet.policy.identity import Identity
from plantangenet.compositor.rule import CompositionRule
from plantangenet.compositor.base import BaseCompositor


class GraphCompositor(BaseCompositor):
    """
    Abstract base for compositing graphs of related objects.
    The 'composition' is the graph itself - nodes, edges, and their relationships.
    """

    def __init__(self):
        super().__init__()
        self.nodes: Dict[str, Any] = {}
        self.edges: Dict[str, List[str]] = {}  # adjacency list
        self.graph_metadata: Dict[str, Any] = {}

    @abstractmethod
    def add_node(self, node_id: str, node: Any, metadata: Optional[Dict] = None):
        """Add a node to the graph."""
        pass

    @abstractmethod
    def add_edge(self, from_node: str, to_node: str, edge_type: str = "default"):
        """Add an edge between nodes."""
        pass

    @abstractmethod
    def compose_graph(self) -> Dict[str, Any]:
        """Generate the current composition of the graph."""
        pass

    def add_composition_rule(self, rule: CompositionRule):
        """Add a rule for transforming the graph composition."""
        self.composition_rules.append(rule)

    def get_neighbors(self, node_id: str) -> List[str]:
        """Get adjacent nodes."""
        return self.edges.get(node_id, [])

    def get_subgraph(self, node_ids: List[str]) -> Dict[str, Any]:
        """Extract a subgraph containing specific nodes."""
        subgraph = {
            "nodes": {nid: self.nodes[nid] for nid in node_ids if nid in self.nodes},
            "edges": {},
            "metadata": {}
        }

        for node_id in node_ids:
            if node_id in self.edges:
                subgraph["edges"][node_id] = [
                    target for target in self.edges[node_id]
                    if target in node_ids
                ]

        return subgraph

    def remove_node(self, node_id: str):
        """Remove a node and all its edges."""
        if node_id in self.nodes:
            del self.nodes[node_id]

        if node_id in self.edges:
            del self.edges[node_id]

        # Remove edges pointing to this node
        for source_node in self.edges:
            if node_id in self.edges[source_node]:
                self.edges[source_node].remove(node_id)

    def _calculate_density(self) -> float:
        """Calculate graph density (edges / possible_edges)."""
        n = len(self.nodes)
        if n <= 1:
            return 0.0

        max_edges = n * (n - 1)  # directed graph
        actual_edges = sum(len(adj) for adj in self.edges.values())
        return actual_edges / max_edges

    def _find_connected_components(self) -> List[List[str]]:
        """Find connected components using DFS."""
        visited = set()
        components = []

        def dfs(node, component):
            if node in visited:
                return
            visited.add(node)
            component.append(node)

            # Visit neighbors (both directions for undirected connectivity)
            for neighbor in self.edges.get(node, []):
                dfs(neighbor, component)

            # Check reverse edges
            for source, targets in self.edges.items():
                if node in targets and source not in visited:
                    dfs(source, component)

        for node in self.nodes:
            if node not in visited:
                component = []
                dfs(node, component)
                if component:
                    components.append(component)

        return components

    def _identify_hubs(self) -> List[str]:
        """Identify nodes with high connectivity (hubs)."""
        if not self.nodes:
            return []

        # Calculate out-degree for each node
        degrees = {node: len(self.edges.get(node, [])) for node in self.nodes}

        # Add in-degree
        for source, targets in self.edges.items():
            for target in targets:
                if target in degrees:
                    degrees[target] += 1

        # Find nodes with above-average connectivity
        avg_degree = sum(degrees.values()) / len(degrees)
        hubs = [node for node, degree in degrees.items() if degree >
                avg_degree]

        return sorted(hubs, key=lambda n: degrees[n], reverse=True)

    def compose(self) -> Dict[str, Any]:
        """Alias for compose_graph for API consistency."""
        return self.compose_graph()

    def transform(self, data, **kwargs) -> Dict[str, Any]:
        """
        Apply graph transformation to input data.
        Default behavior: if data is a dict with nodes/edges, merge into graph.
        Returns the composed graph representation.
        """
        if isinstance(data, dict):
            if "nodes" in data:
                self.nodes.update(data["nodes"])
            if "edges" in data:
                for node_id, edge_list in data["edges"].items():
                    if node_id not in self.edges:
                        self.edges[node_id] = []
                    self.edges[node_id].extend(edge_list)

        return self.compose()


class AgentSquad(GraphCompositor):
    """
    A specialized graph compositor for Agent objects.
    The composition is the live graph of agent relationships and communication channels.
    """

    def __init__(self, name: Optional[str] = None, policy: Optional[Policy] = None):
        super().__init__()
        self.name = name or f"squad_{uuid.uuid4().hex[:8]}"
        self.squad_policy = policy
        self._sessions: Dict[str, Session] = {}

        # Agent-specific graph metadata
        self.graph_metadata.update({
            "squad_type": "agent_graph",
            "squad_name": self.name,
            "created_at": time.time(),
            "communication_channels": {},
            "trust_relationships": {},
            "policy_propagation": {}
        })

    def add_node(self, node_id: str, node: Agent, metadata: Optional[Dict] = None):
        """Add an agent as a node in the squad graph."""
        if not isinstance(node, Agent):
            raise TypeError("AgentSquad nodes must be Agent instances")

        self.nodes[node_id] = node
        self.edges[node_id] = []  # Initialize adjacency list

        # Store agent-specific metadata
        node_metadata = {
            "agent_type": type(node).__name__,
            "agent_id": node.id,
            "agent_name": getattr(node, 'name', 'unnamed'),
            "capabilities": getattr(node, 'capabilities', {}),
            "status": "active",
            "join_time": time.time(),
            **(metadata or {})
        }
        self.graph_metadata[f"node_{node_id}"] = node_metadata

    def add_edge(self, from_node: str, to_node: str, edge_type: str = "communication"):
        """Add a relationship edge between agents."""
        if from_node not in self.nodes or to_node not in self.nodes:
            raise ValueError("Both agents must be nodes in the graph")

        if to_node not in self.edges[from_node]:
            self.edges[from_node].append(to_node)

        # Track edge metadata
        edge_key = f"{from_node}->{to_node}"
        self.graph_metadata["communication_channels"][edge_key] = {
            "edge_type": edge_type,
            "established": time.time(),
            "message_count": 0
        }

    def compose_graph(self) -> Dict[str, Any]:
        """
        Generate the current composition of the agent graph.
        This includes agent states, relationships, and computed graph properties.
        """
        base_composition = {
            "squad_name": self.name,
            "timestamp": time.time(),
            "nodes": {},
            "edges": dict(self.edges),
            "graph_properties": self._compute_graph_properties(),
            "metadata": dict(self.graph_metadata)
        }

        # Include current agent states
        for node_id, agent in self.nodes.items():
            if isinstance(agent, Agent):
                base_composition["nodes"][node_id] = {
                    "agent_id": agent.id,
                    "agent_name": getattr(agent, 'name', 'unnamed'),
                    "agent_type": type(agent).__name__,
                    "namespace": getattr(agent, 'namespace', 'unknown'),
                    "capabilities": getattr(agent, 'capabilities', {}),
                    "current_status": "active"  # Could query agent.status if available
                }
            else:
                # Handle non-agent nodes (like sessions)
                base_composition["nodes"][node_id] = {
                    "object_type": type(agent).__name__,
                    "object_id": getattr(agent, 'id', str(agent)),
                    "current_status": "active"
                }

        # Apply composition rules to transform the graph representation
        composition = base_composition
        for rule in self.composition_rules:
            # No frame for graph composition
            composition = rule(composition, None)

        return composition

    def _compute_graph_properties(self) -> Dict[str, Any]:
        """Compute graph-level properties like connectivity, centrality, etc."""
        return {
            "node_count": len(self.nodes),
            "edge_count": sum(len(adj) for adj in self.edges.values()),
            "density": self._calculate_density(),
            "connected_components": self._find_connected_components(),
            "communication_hubs": self._identify_hubs(),
            "session_count": len(self._sessions)
        }

    # Session management (preserving existing Squad functionality)
    def create_session(self, identity: Identity, policy: Optional[Policy] = None,
                       metadata: Optional[Dict[str, Any]] = None) -> Session:
        """Create a session and add it as a special node in the graph."""
        session_id = str(uuid.uuid4())
        effective_policy = policy or self.squad_policy or Policy()

        session = Session(
            id=session_id,
            policy=effective_policy,
            identity=identity,
            metadata=metadata or {}
        )

        # Add session as a special type of node
        self.add_session_node(session)

        self._sessions[session_id] = session
        return session

    def add_session_node(self, session: Session):
        """Add a session as a node in the graph."""
        session_node_id = f"session_{session._id}"
        self.nodes[session_node_id] = session
        self.edges[session_node_id] = []

        identity_id = getattr(session.identity, 'id',
                              None) if session.identity else None
        self.graph_metadata[f"node_{session_node_id}"] = {
            "node_type": "session",
            "session_id": session._id,
            "identity_id": identity_id,
            "created_at": time.time()
        }

    def add_agent_to_session(self, agent: Agent, session: Session):
        """Add an agent to a session and create graph edges."""
        agent_id = f"agent_{agent.id}"
        session_id = f"session_{session._id}"

        # Add agent as node if not already present
        if agent_id not in self.nodes:
            self.add_node(agent_id, agent)

        # Create edge from session to agent (session "manages" agent)
        self.add_edge(session_id, agent_id, "session_membership")

    def get_session_agents(self, session: Session) -> List[Agent]:
        """Get all agents connected to a session."""
        session_node_id = f"session_{session._id}"
        if session_node_id not in self.edges:
            return []

        agents = []
        for agent_node_id in self.edges[session_node_id]:
            if agent_node_id in self.nodes:
                node = self.nodes[agent_node_id]
                if isinstance(node, Agent):
                    agents.append(node)

        return agents

    def remove_agent(self, agent: Agent):
        """Remove an agent from the squad graph."""
        agent_node_id = f"agent_{agent.id}"
        self.remove_node(agent_node_id)

        # Clean up metadata
        metadata_key = f"node_{agent_node_id}"
        if metadata_key in self.graph_metadata:
            del self.graph_metadata[metadata_key]


# Graph-specific composition rules
class GraphCompositionRule(CompositionRule):
    """Base class for rules that operate on graph compositions."""

    @abstractmethod
    def __call__(self, graph_data: Dict[str, Any], context: Any = None) -> Dict[str, Any]:
        pass


class AgentFilterRule(GraphCompositionRule):
    """Filter agents by capabilities or status."""

    def __init__(self, filter_predicate: Callable[[Dict], bool]):
        self.filter_predicate = filter_predicate

    def __call__(self, graph_data: Dict[str, Any], context: Any = None) -> Dict[str, Any]:
        filtered_nodes = {}
        for node_id, node_data in graph_data["nodes"].items():
            if self.filter_predicate(node_data):
                filtered_nodes[node_id] = node_data

        # Update edges to only include connections between filtered nodes
        filtered_edges = {}
        for node_id in filtered_nodes:
            if node_id in graph_data["edges"]:
                filtered_edges[node_id] = [
                    target for target in graph_data["edges"][node_id]
                    if target in filtered_nodes
                ]

        graph_data["nodes"] = filtered_nodes
        graph_data["edges"] = filtered_edges
        return graph_data


class CommunicationFlowRule(GraphCompositionRule):
    """Add communication flow analysis to the composition."""

    def __call__(self, graph_data: Dict[str, Any], context: Any = None) -> Dict[str, Any]:
        communication_flows = self._analyze_communication_patterns(graph_data)
        graph_data["communication_analysis"] = communication_flows
        return graph_data

    def _analyze_communication_patterns(self, graph_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze communication patterns in the graph."""
        edges = graph_data["edges"]
        nodes = graph_data["nodes"]

        # Calculate communication metrics
        total_connections = sum(len(targets) for targets in edges.values())
        avg_connections = total_connections / len(nodes) if nodes else 0

        # Find most connected nodes
        connection_counts = {node: len(edges.get(node, [])) for node in nodes}
        most_connected = sorted(connection_counts.items(),
                                key=lambda x: x[1], reverse=True)[:3]

        return {
            "total_connections": total_connections,
            "average_connections_per_node": avg_connections,
            "most_connected_nodes": most_connected,
            "communication_density": total_connections / (len(nodes) ** 2) if nodes else 0
        }


class SessionAnalysisRule(GraphCompositionRule):
    """Add session-specific analysis to the composition."""

    def __call__(self, graph_data: Dict[str, Any], context: Any = None) -> Dict[str, Any]:
        session_analysis = self._analyze_sessions(graph_data)
        graph_data["session_analysis"] = session_analysis
        return graph_data

    def _analyze_sessions(self, graph_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze session distribution and relationships."""
        nodes = graph_data["nodes"]
        edges = graph_data["edges"]

        # Count sessions vs agents
        sessions = [nid for nid, node in nodes.items(
        ) if "session" in node.get("object_type", "")]
        agents = [nid for nid, node in nodes.items() if node.get("agent_type")]

        # Calculate session-agent relationships
        session_agent_connections = 0
        for session_node in sessions:
            if session_node in edges:
                session_agent_connections += len([
                    target for target in edges[session_node]
                    if target in agents
                ])

        return {
            "session_count": len(sessions),
            "agent_count": len(agents),
            "session_agent_connections": session_agent_connections,
            "average_agents_per_session": session_agent_connections / len(sessions) if sessions else 0
        }


class MLCompositor(BaseCompositor):
    """
    Experimental compositor for ML/dataflow/feature engineering pipelines.

    Possible roles:
    - Compose feature tensors from multiple sources
    - Apply ML-specific transformation rules (normalization, encoding, etc)
    - Integrate with model training/inference pipelines
    - Support graph-based or sequential data flows
    - Provide hooks for feature selection, importance, and explainability

    This is a stub for future expansion.
    """

    def __init__(self):
        super().__init__()
        # Add ML/dataflow-specific state here

    def compose(self, *args, **kwargs):
        raise NotImplementedError(
            "MLCompositor is a stub. Define your ML/dataflow pipeline here.")
