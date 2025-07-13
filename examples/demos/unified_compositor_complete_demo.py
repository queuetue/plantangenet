#!/usr/bin/env python3
"""
Comprehensive demo of the unified Compositor architecture.
Shows ML, Graph, and Framebuffer compositors working together with the same interface.
"""

import numpy as np
from plantangenet.policy.identity import Identity
from plantangenet.agents.agent import Agent
from plantangenet.compositor.graph_compositor import AgentSquad
from plantangenet.compositor.fb_types import ImmediateModeFBCompositor
from plantangenet.compositor.ml_types import ClassifierCompositor, GenerativeCompositor
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'python'))


class DemoClassifier(ClassifierCompositor):
    """Demo classifier for unified interface testing."""

    def __init__(self):
        super().__init__()
        self.model_trained = False

    def fit(self, X, y=None):
        self.model_trained = True
        print(f"🧠 Classifier trained on {len(X) if X else 0} samples")

    def predict(self, X):
        if not self.model_trained:
            return ["untrained"] * len(X)
        return ["positive" if i % 2 == 0 else "negative" for i in range(len(X))]

    def update(self, X, y=None):
        print(f"🔄 Classifier updated with {len(X) if X else 0} new samples")


class DemoGenerator(GenerativeCompositor):
    """Demo generator for unified interface testing."""

    def __init__(self):
        super().__init__()
        self.creativity = 0.5

    def fit(self, X, y=None):
        self.creativity = min(1.0, self.creativity + 0.1)
        print(f"🎨 Generator creativity increased to {self.creativity:.1f}")

    def predict(self, X):
        return [f"generated_from_{x}" for x in X]

    def update(self, X, y=None):
        print(f"✨ Generator refined with {len(X) if X else 0} examples")

    def generate(self, context=None):
        if context:
            return f"creative_response_to_{context}"
        return f"random_creation_{np.random.randint(1000)}"


class DemoAgent(Agent):
    """Simple agent for graph testing."""

    def __init__(self, agent_name: str, **kwargs):
        super().__init__(**kwargs)
        self.agent_name = agent_name

    async def update(self) -> bool:
        return True

    @property
    def capabilities(self):
        return {"name": {self.agent_name}, "type": {"demo"}}


def demo_unified_compositor_interface():
    """Demonstrate the unified compositor interface across all types."""
    print("🎯 Unified Compositor Interface Demo")
    print("=" * 60)

    # Create different compositor types
    classifier = DemoClassifier()
    generator = DemoGenerator()
    framebuffer = ImmediateModeFBCompositor(width=100, height=100)
    graph = AgentSquad(name="demo_squad")

    print("🔧 Created 4 different compositor types:")
    print("   • ML Classifier")
    print("   • ML Generator")
    print("   • Framebuffer (UI)")
    print("   • Graph (Agent Squad)")
    print()

    # Test unified transform interface
    print("🔄 Testing unified transform() interface:")
    print("-" * 40)

    # 1. ML Classifier transform
    ml_data = ["sample1", "sample2", "sample3"]
    classifier.compose(ml_data)  # Train first
    ml_result = classifier.transform(ml_data)
    print(f"📊 Classifier transform: {ml_data} → {ml_result}")

    # 2. ML Generator transform
    gen_data = ["prompt1", "prompt2"]
    gen_result = generator.transform(gen_data)
    print(f"🎨 Generator transform: {gen_data} → {gen_result}")

    # 3. Framebuffer transform (with events)
    ui_events = [{"type": "button_click", "id": "demo_button"}]
    fb_result = framebuffer.transform(ui_events)
    print(
        f"🖼️  Framebuffer transform: events → UI state with {len(fb_result['widgets'])} widgets")

    # 4. Graph transform (with graph data)
    agent1 = DemoAgent("Alice")
    agent2 = DemoAgent("Bob")
    graph_data = {
        "nodes": {"alice": agent1, "bob": agent2},
        "edges": {"alice": ["bob"]}
    }
    graph_result = graph.transform(graph_data)
    print(
        f"📊 Graph transform: added {len(graph_data['nodes'])} nodes → composition with {len(graph_result['nodes'])} total nodes")

    print()
    print("✅ All compositor types use the same transform() interface!")
    print()


def demo_unified_compose_interface():
    """Demonstrate the unified compose interface."""
    print("🎼 Unified Compose Interface Demo")
    print("=" * 60)

    classifier = DemoClassifier()
    generator = DemoGenerator()
    framebuffer = ImmediateModeFBCompositor(width=50, height=50)
    graph = AgentSquad(name="compose_squad")

    print("🎵 Testing unified compose() interface:")
    print("-" * 40)

    # Test compose for each type
    training_data = ["train1", "train2", "train3"]

    # ML Classifier compose
    classifier_result = classifier.compose(training_data)
    print(f"📊 Classifier compose: returns {type(classifier_result).__name__}")

    # ML Generator compose
    generator_result = generator.compose(training_data)
    print(f"🎨 Generator compose: returns {type(generator_result).__name__}")

    # Framebuffer compose
    fb_result = framebuffer.compose()
    print(f"🖼️  Framebuffer compose: returns array shape {fb_result.shape}")

    # Graph compose
    graph.add_node("test_agent", DemoAgent("TestAgent"))
    graph_result = graph.compose()
    print(f"📊 Graph compose: returns dict with {len(graph_result)} keys")

    print()
    print("✅ All compositor types implement compose() consistently!")
    print()


def demo_compositor_chaining():
    """Demonstrate chaining compositors together."""
    print("⛓️  Compositor Chaining Demo")
    print("=" * 60)

    # Create a pipeline: Generate → Classify → Visualize
    generator = DemoGenerator()
    classifier = DemoClassifier()
    visualizer = ImmediateModeFBCompositor(width=200, height=100)

    print("🔗 Creating a 3-stage compositor pipeline:")
    print("   Generate → Classify → Visualize")
    print()

    # Stage 1: Generate content
    generated = generator.generate("create_samples")
    print(f"🎨 Stage 1 - Generated: {generated}")

    # Stage 2: Classify the generated content
    classifier.compose([generated])  # Train on the generated sample
    classification = classifier.transform([generated])
    print(f"📊 Stage 2 - Classified: {classification}")

    # Stage 3: Visualize the result
    visualizer.begin_frame()

    # Create UI based on classification
    if "positive" in classification[0]:
        button_color = "✅ Positive Result"
        ui_events = [{"type": "button_click", "id": "positive_btn"}]
    else:
        button_color = "❌ Negative Result"
        ui_events = [{"type": "button_click", "id": "negative_btn"}]

    clicked = visualizer.button(button_color, 10, 10, 150, 30)
    visualizer.end_frame()

    viz_result = visualizer.transform(ui_events)
    print(
        f"🖼️  Stage 3 - Visualized: UI with {len(viz_result['widgets'])} widgets")

    print()
    print("✅ Compositors successfully chained together!")
    print("✨ Each stage uses the same unified interface!")
    print()


def demo_real_world_scenario():
    """Demonstrate a real-world scenario using multiple compositor types."""
    print("🌍 Real-World Scenario Demo")
    print("=" * 60)
    print("Scenario: Interactive ML Training Dashboard")
    print()

    # Components
    model = DemoClassifier()
    data_generator = DemoGenerator()
    ui = ImmediateModeFBCompositor(width=400, height=300)
    agent_squad = AgentSquad(name="ml_training_squad")

    # Add training agents to the squad
    trainer_agent = DemoAgent("DataTrainer")
    evaluator_agent = DemoAgent("ModelEvaluator")
    agent_squad.add_node("trainer", trainer_agent)
    agent_squad.add_node("evaluator", evaluator_agent)
    agent_squad.add_edge("trainer", "evaluator", "data_flow")

    print("🏗️  Dashboard Components:")
    print(f"   • ML Model: {type(model).__name__}")
    print(f"   • Data Generator: {type(data_generator).__name__}")
    print(f"   • UI Framework: {type(ui).__name__}")
    print(
        f"   • Agent Squad: {agent_squad.name} with {len(agent_squad.nodes)} agents")
    print()

    # Simulation loop
    print("🔄 Running interactive training simulation:")
    print("-" * 50)

    for round_num in range(3):
        print(f"\n📈 Training Round {round_num + 1}")

        # Generate training data
        synthetic_data = [data_generator.generate(
            f"round_{round_num}_sample_{i}") for i in range(3)]
        print(f"   🎨 Generated {len(synthetic_data)} training samples")

        # Train model
        model.compose(synthetic_data)
        predictions = model.transform(synthetic_data[:2])
        print(f"   🧠 Model predictions: {predictions}")

        # Update agent squad with training progress
        training_progress = {
            "nodes": {f"round_{round_num}_data": {"samples": len(synthetic_data), "accuracy": 0.8 + round_num * 0.1}},
            "edges": {"trainer": [f"round_{round_num}_data"]}
        }
        squad_state = agent_squad.transform(training_progress)
        print(f"   📊 Squad updated: {len(squad_state['nodes'])} total nodes")

        # Update UI
        ui.begin_frame()
        train_clicked = ui.button(
            f"Train Round {round_num + 2}", 50, 50 + round_num * 40, 120, 30)
        ui.end_frame()

        if train_clicked:
            print(
                f"   🖱️  User clicked train button for round {round_num + 2}")

    print("\n✅ Interactive ML training dashboard simulation complete!")
    print("🎯 All compositor types working together seamlessly!")
    print()


if __name__ == "__main__":
    print("🚀 Unified Compositor Architecture Demo")
    print("=" * 80)
    print("Demonstrating ML, Graph, and Framebuffer compositors with unified interface")
    print()

    try:
        demo_unified_compositor_interface()
        demo_unified_compose_interface()
        demo_compositor_chaining()
        demo_real_world_scenario()

        print("🎉 All unified compositor demos completed successfully!")
        print("✨ Your compositor architecture is ready for:")
        print("   • Machine Learning workloads")
        print("   • Graph-based agent orchestration")
        print("   • Immediate mode UI development")
        print("   • Unified data transformation pipelines")
        print("   • Real-time interactive applications")

    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
