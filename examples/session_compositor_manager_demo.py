#!/usr/bin/env python3
"""
Demo of Session as compositor manager.
Shows how Session coordinates ML, Graph, and Framebuffer compositors with shared state.
"""

import numpy as np
from plantangenet.agents.agent import Agent
from plantangenet.squad.graph_compositor import AgentSquad
from plantangenet.compositor.fb_types import ImmediateModeFBCompositor
from plantangenet.compositor.ml_types import ClassifierCompositor, GenerativeCompositor
from plantangenet.policy.identity import Identity
from plantangenet.policy.policy import Policy
from plantangenet.session.session import Session
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'python'))


class GameClassifier(ClassifierCompositor):
    """Example game outcome classifier."""

    def __init__(self):
        super().__init__()
        self.trained = False

    def fit(self, X, y=None):
        self.trained = True
        print(f"🎯 Game classifier trained on {len(X)} game samples")

    def predict(self, X):
        if not self.trained:
            return ["unknown"] * len(X)
        # Simple mock prediction based on data patterns
        return ["win" if "victory" in str(sample).lower() else "loss" for sample in X]

    def update(self, X, y=None):
        print(f"📈 Classifier updated with {len(X)} new samples")


class MusicGenerator(GenerativeCompositor):
    """Example music/content generator."""

    def __init__(self):
        super().__init__()
        self.style = "classical"

    def fit(self, X, y=None):
        self.style = "learned" if X else "classical"
        print(
            f"🎵 Music generator learned from {len(X) if X else 0} samples, style: {self.style}")

    def predict(self, X):
        return [f"generated_melody_from_{sample}" for sample in X]

    def update(self, X, y=None):
        print(f"🎶 Generator refined with {len(X)} new examples")

    def generate(self, context=None):
        if context:
            return f"🎼 Generated {self.style} music for: {context}"
        return f"🎼 Random {self.style} composition #{np.random.randint(1000)}"


class DemoAgent(Agent):
    """Demo agent for squad management."""

    def __init__(self, agent_name: str, role: str = "player", **kwargs):
        super().__init__(**kwargs)
        self.agent_name = agent_name
        self.role = role
        self.performance_score = 0.5

    async def update(self) -> bool:
        # Simulate performance changes
        self.performance_score = min(
            1.0, max(0.0, self.performance_score + np.random.uniform(-0.1, 0.1)))
        return True

    @property
    def capabilities(self):
        return {
            "name": {self.agent_name},
            "role": {self.role},
            "performance": {f"{self.performance_score:.2f}"}
        }


def demo_session_compositor_coordination():
    """Demonstrate Session coordinating multiple compositor types."""
    print("🎮 Session Compositor Coordination Demo")
    print("=" * 60)

    # Create session
    identity = Identity(id="game_master", nickname="Game Master", roles=[])
    policy = Policy(logger=None, namespace="game_session")
    session = Session(id="game_session_001", policy=policy, identity=identity)

    print(f"📋 Created session: {session._id}")
    print(f"👤 Identity: {identity.nickname}")
    print()

    # Create and add compositors
    game_classifier = GameClassifier()
    music_generator = MusicGenerator()
    ui_compositor = ImmediateModeFBCompositor(width=800, height=600)
    player_squad = AgentSquad(name="player_squad")

    session.add_compositor("classifier", game_classifier)
    session.add_compositor("generator", music_generator)
    session.add_compositor("ui", ui_compositor)
    session.add_compositor("squad", player_squad)

    print("🔧 Added compositors to session:")
    for name, comp_type in session.list_compositors().items():
        print(f"   • {name}: {comp_type}")
    print()

    # Add agents to squad
    agents = [
        DemoAgent("Alice", "attacker", namespace="game", logger=None),
        DemoAgent("Bob", "defender", namespace="game", logger=None),
        DemoAgent("Charlie", "midfielder", namespace="game", logger=None)
    ]

    for i, agent in enumerate(agents):
        player_squad.add_node(f"player_{i}", agent)

    player_squad.add_edge("player_0", "player_1", "teammate")
    player_squad.add_edge("player_1", "player_2", "teammate")

    print(f"⚽ Added {len(agents)} players to squad with team relationships")
    print()

    return session, game_classifier, music_generator, ui_compositor, player_squad


def demo_coordinated_data_flow():
    """Demonstrate coordinated data flow through multiple compositors."""
    session, classifier, generator, ui, squad = demo_session_compositor_coordination()

    print("🔄 Coordinated Data Flow Demo")
    print("=" * 60)

    # Set up shared state for coordination
    session.set_shared_state("game_mode", "competitive")
    session.set_shared_state("current_round", 1)
    session.set_shared_state("player_count", 3)

    print("🌐 Set shared state:")
    for key, value in session.get_shared_state().items():
        print(f"   • {key}: {value}")
    print()

    # Simulate game rounds with coordinated compositor updates
    for round_num in range(1, 4):
        print(f"🎯 Round {round_num}")
        print("-" * 30)

        # Update shared state
        session.set_shared_state("current_round", round_num)

        # 1. Generate game events
        game_events = [
            f"round_{round_num}_player_action",
            f"round_{round_num}_team_strategy",
            f"round_{round_num}_victory_attempt"
        ]

        # 2. Transform data through all compositors
        data_map = {
            "classifier": game_events,
            "generator": [f"round_{round_num}_context"],
            "ui": [{"type": "round_update", "round": round_num}],
            "squad": {
                "nodes": {f"round_{round_num}_data": {"round": round_num, "events": len(game_events)}},
                "edges": {}
            }
        }

        print(f"📊 Transforming data through all compositors...")
        results = session.transform_all_compositors(data_map)

        print(f"   🎯 Classifier predictions: {results['classifier']}")
        print(
            f"   🎵 Generated content: {generator.generate(f'round_{round_num}')}")
        print(
            f"   🖼️  UI state updated: {len(results['ui']['widgets'])} widgets")
        print(
            f"   👥 Squad composition: {len(results['squad']['nodes'])} total nodes")

        # 3. Use shared state to coordinate between compositors
        if "win" in str(results['classifier']):
            session.set_shared_state("last_victory_round", round_num)
            victory_music = generator.generate("victory_celebration")
            print(f"   🏆 Victory detected! Generated: {victory_music}")

        print()

    # Final coordination: compose all outputs
    print("🎼 Final Composition Coordination")
    print("-" * 30)

    final_outputs = session.compose_all_compositors()

    print("📋 Final compositor outputs:")
    for name, output in final_outputs.items():
        if name == "squad":
            print(
                f"   • {name}: {len(output['nodes'])} nodes, {len(output['edges'])} edge groups")
        elif name == "ui":
            print(f"   • {name}: framebuffer shape {output.shape}")
        else:
            print(f"   • {name}: {type(output).__name__}")

    # Show shared state coordination
    final_state = session.get_shared_state()
    print(f"\n🌐 Final shared state: {final_state}")

    return session


def demo_real_time_coordination():
    """Demonstrate real-time coordination between compositors."""
    session, classifier, generator, ui, squad = demo_session_compositor_coordination()

    print("⚡ Real-Time Coordination Demo")
    print("=" * 60)

    # Simulate real-time events flowing between compositors
    events = [
        {"type": "player_action", "player": "Alice", "action": "score"},
        {"type": "team_event", "event": "victory_sequence"},
        {"type": "ui_interaction", "element": "celebration_button", "clicked": True},
        {"type": "music_request", "mood": "triumphant"}
    ]

    for i, event in enumerate(events):
        print(f"⚡ Event {i+1}: {event['type']}")

        # Route event to appropriate compositors
        if event['type'] == "player_action":
            # Update squad with player performance
            result = session.transform_compositor("squad", {
                "nodes": {f"event_{i}": event},
                "edges": {}
            })
            print(f"   👥 Squad updated: {len(result['nodes'])} total nodes")

        elif event['type'] == "team_event":
            # Classify the event outcome
            result = session.transform_compositor(
                "classifier", [event['event']])
            print(f"   🎯 Event classified as: {result[0]}")

            # Generate appropriate music
            music = generator.generate(event['event'])
            print(f"   🎵 Generated music: {music}")

        elif event['type'] == "ui_interaction":
            # Update UI state
            ui_events = [{"type": "button_click", "id": event['element']}]
            result = session.transform_compositor("ui", ui_events)
            print(f"   🖼️  UI updated: button interaction processed")

        elif event['type'] == "music_request":
            # Generate music and share with UI
            music = generator.generate(event['mood'])
            session.set_shared_state("current_music", music)
            print(f"   🎶 Music shared: {music}")

        print()

    # Show how compositors can access shared state
    print("🔗 Compositor State Sharing:")
    print(f"   Current music: {session.get_shared_state('current_music')}")
    print(
        f"   All outputs available: {list(session.get_all_compositor_outputs().keys())}")

    return session


def demo_error_handling_and_resilience():
    """Demonstrate error handling and resilience in compositor coordination."""
    session, classifier, generator, ui, squad = demo_session_compositor_coordination()

    print("🛡️  Error Handling & Resilience Demo")
    print("=" * 60)

    # Test broadcast with some compositors failing
    class FailingCompositor(ImmediateModeFBCompositor):
        def transform(self, data, **kwargs):
            if "fail" in str(data):
                raise ValueError("Simulated compositor failure")
            return super().transform(data, **kwargs)

    session.add_compositor(
        "failing_ui", FailingCompositor(width=100, height=100))

    # Broadcast data that causes some compositors to fail
    test_data = "test_data_with_fail_trigger"
    results = session.broadcast_to_compositors(test_data)

    print("🧪 Broadcast results with simulated failures:")
    for name, result in results.items():
        if isinstance(result, dict) and "error" in result:
            print(f"   ❌ {name}: {result['error']}")
        else:
            print(f"   ✅ {name}: success")

    print()

    # Test graceful degradation
    print("🔄 Testing graceful degradation:")

    # Remove a compositor and verify system continues working
    session.remove_compositor("failing_ui")
    remaining_compositors = session.list_compositors()
    print(
        f"   Removed failing compositor, {len(remaining_compositors)} remain active")

    # Continue processing with remaining compositors
    healthy_results = session.broadcast_to_compositors("healthy_data")
    print(
        f"   All remaining compositors processed successfully: {len(healthy_results)} results")

    return session


if __name__ == "__main__":
    print("🚀 Session Compositor Manager Demo")
    print("=" * 80)
    print("Demonstrating Session as central coordinator for multiple compositor types")
    print()

    try:
        # Run all demos
        session1 = demo_coordinated_data_flow()
        print("\n" + "="*80 + "\n")

        session2 = demo_real_time_coordination()
        print("\n" + "="*80 + "\n")

        session3 = demo_error_handling_and_resilience()

        print("\n🎉 All demos completed successfully!")
        print("\n✨ Session successfully coordinates:")
        print("   • ML compositors (classification, generation)")
        print("   • Graph compositors (agent squads)")
        print("   • Framebuffer compositors (UI)")
        print("   • Shared state management")
        print("   • Real-time event coordination")
        print("   • Error handling and resilience")
        print("   • Unified data transformation pipelines")

    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
