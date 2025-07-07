# Unified Compositor/Squad Architecture Proposal

## Vision: "A composition is the squad graph"

The core insight is that a `Squad` should be a specialized `Compositor` where the "composition" is the living graph of agent relationships, not just static data.

## Current State Analysis

### Existing Compositor
- **Purpose**: Transforms time-series data using composition rules
- **Core**: `BasicCompositor` applies `CompositionRule`s to `MultiAxisFrame` data
- **Output**: Transformed dictionaries representing "views" of data
- **Pattern**: `collector -> rules -> composed_data`

### Existing Squad
- **Purpose**: Manages collections of agents and sessions
- **Core**: Group-based management with policy enforcement
- **Output**: Session coordination, agent lifecycle, policy evaluation
- **Pattern**: `sessions -> agents -> policy -> coordination`

## Unified Architecture Design

### 1. Abstract Graph Compositor Base

```python
class GraphCompositor(ABC):
    """
    Abstract base for compositing graphs of related objects.
    The 'composition' is the graph itself - nodes, edges, and their relationships.
    """
    
    def __init__(self):
        self.nodes: Dict[str, Any] = {}
        self.edges: Dict[str, List[str]] = {}  # adjacency list
        self.composition_rules: List[CompositionRule] = []
        self.graph_metadata: Dict[str, Any] = {}
    
    @abstractmethod
    def add_node(self, node_id: str, node: Any, metadata: Dict = None):
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
        # Implementation for subgraph extraction
        pass
```

### 2. AgentSquad as Specialized Graph Compositor

```python
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
            "communication_channels": {},
            "trust_relationships": {},
            "policy_propagation": {}
        })
    
    def add_node(self, node_id: str, agent: Agent, metadata: Dict = None):
        """Add an agent as a node in the squad graph."""
        if not isinstance(agent, Agent):
            raise TypeError("AgentSquad nodes must be Agent instances")
        
        self.nodes[node_id] = agent
        self.edges[node_id] = []  # Initialize adjacency list
        
        # Store agent-specific metadata
        node_metadata = {
            "agent_type": type(agent).__name__,
            "capabilities": getattr(agent, 'capabilities', {}),
            "status": "active",
            "join_time": time.time(),
            **(metadata or {})
        }
        self.graph_metadata[f"node_{node_id}"] = node_metadata
    
    def add_edge(self, from_agent: str, to_agent: str, edge_type: str = "communication"):
        """Add a relationship edge between agents."""
        if from_agent not in self.nodes or to_agent not in self.nodes:
            raise ValueError("Both agents must be nodes in the graph")
        
        if to_agent not in self.edges[from_agent]:
            self.edges[from_agent].append(to_agent)
        
        # Track edge metadata
        edge_key = f"{from_agent}->{to_agent}"
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
            base_composition["nodes"][node_id] = {
                "agent_id": agent.id,
                "agent_name": getattr(agent, 'name', 'unnamed'),
                "status": getattr(agent, 'status', {}),
                "capabilities": getattr(agent, 'capabilities', {})
            }
        
        # Apply composition rules to transform the graph representation
        composition = base_composition
        for rule in self.composition_rules:
            composition = rule(composition, None)  # No frame for graph composition
        
        return composition
    
    def _compute_graph_properties(self) -> Dict[str, Any]:
        """Compute graph-level properties like connectivity, centrality, etc."""
        return {
            "node_count": len(self.nodes),
            "edge_count": sum(len(adj) for adj in self.edges.values()),
            "density": self._calculate_density(),
            "connected_components": self._find_connected_components(),
            "communication_hubs": self._identify_hubs()
        }
    
    # Session management (existing Squad functionality)
    def create_session(self, identity: Identity, policy: Optional[Policy] = None) -> Session:
        """Create a session and add it as a special node in the graph."""
        session_id = str(uuid.uuid4())
        effective_policy = policy or self.squad_policy or Policy()
        
        session = Session(
            id=session_id,
            policy=effective_policy,
            identity=identity
        )
        
        # Add session as a special type of node
        self.add_node(f"session_{session_id}", session, {
            "node_type": "session",
            "identity_id": identity.id
        })
        
        self._sessions[session_id] = session
        return session
    
    def add_agent_to_session(self, agent: Agent, session: Session):
        """Add an agent to a session and create graph edges."""
        agent_id = f"agent_{agent.id}"
        session_id = f"session_{session._id}"
        
        # Add agent as node if not already present
        if agent_id not in self.nodes:
            self.add_node(agent_id, agent)
        
        # Create edge from session to agent
        self.add_edge(session_id, agent_id, "session_membership")
```

### 3. Data Compositor (Existing Pattern)

```python
class DataCompositor(GraphCompositor):
    """
    Specialized graph compositor for time-series data composition.
    Maintains backward compatibility with existing Compositor usage.
    """
    
    def __init__(self, collector: TimeSeriesCollector):
        super().__init__()
        self.collector = collector
        self.graph_metadata.update({
            "compositor_type": "data_flow",
            "data_source": "time_series_collector"
        })
    
    def add_node(self, node_id: str, axis_frame: Any, metadata: Dict = None):
        """Add an axis frame as a node."""
        # Implementation for data-specific nodes
        pass
    
    def compose_graph(self) -> Dict[str, Any]:
        """Compose a graph representation of data flow."""
        # This could represent data dependencies, transformations, etc.
        pass
    
    # Backward compatibility methods
    def compose_frame(self, tick: int) -> Optional[Dict[str, Any]]:
        """Maintain backward compatibility with existing BasicCompositor API."""
        # Delegate to original logic while building graph representation
        pass
```

### 4. Composition Rules for Graphs

```python
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
        
        graph_data["nodes"] = filtered_nodes
        return graph_data

class CommunicationFlowRule(GraphCompositionRule):
    """Add communication flow analysis to the composition."""
    
    def __call__(self, graph_data: Dict[str, Any], context: Any = None) -> Dict[str, Any]:
        # Compute message flows, communication patterns, etc.
        communication_flows = self._analyze_communication_patterns(graph_data)
        graph_data["communication_analysis"] = communication_flows
        return graph_data
```

## Benefits of This Unified Approach

### 1. **Conceptual Clarity**
- `Squad` *is* a `Compositor` for agent graphs
- The "composition" is the living graph of relationships
- Same conceptual model applies to different domains (data, agents, resources)

### 2. **Code Reuse**
- Graph operations (traversal, analysis, filtering) shared across all compositor types
- Composition rules can be applied to any graph type
- Consistent API for different kinds of "compositions"

### 3. **Flexibility**
- Can represent complex agent relationships (hierarchies, communication channels, trust networks)
- Graph-based analysis (centrality, clustering, flow analysis)
- Dynamic graph evolution as agents join/leave

### 4. **Backward Compatibility**
- Existing `BasicCompositor` becomes `DataCompositor`
- Existing `Squad` functionality preserved but unified under graph model
- Composition rules work across different compositor types

## Implementation Steps

1. **Create `GraphCompositor` base class** with core graph operations
2. **Refactor `Squad` to inherit from `GraphCompositor`** 
3. **Create `DataCompositor`** that wraps existing `BasicCompositor` logic
4. **Implement graph-specific composition rules**
5. **Add graph analysis capabilities** (connectivity, centrality, flow analysis)
6. **Update tests** to verify unified behavior
7. **Create examples** demonstrating agent graph composition

## Usage Examples

```python
# Agent squad as graph compositor
squad = AgentSquad(name="simulation_squad")

# Add agents as nodes
squad.add_node("player1", player1_agent)
squad.add_node("referee", referee_agent)

# Create relationships
squad.add_edge("referee", "player1", "game_coordination")

# Add composition rules
squad.add_composition_rule(AgentFilterRule(lambda a: a["status"] == "active"))
squad.add_composition_rule(CommunicationFlowRule())

# Get current graph composition
composition = squad.compose_graph()
print(f"Active agents: {len(composition['nodes'])}")
print(f"Communication flows: {composition['communication_analysis']}")
```

## Conclusion

This unified architecture treats "composition" as the graph itself - whether it's a graph of agents, data flows, or other relationships. The `Squad` becomes a specialized graph compositor that manages agent relationships and coordination, while maintaining all existing session and policy functionality.

The key insight is that both data composition and agent coordination are fundamentally about managing graphs of relationships and applying transformation rules to understand and manipulate those relationships.
