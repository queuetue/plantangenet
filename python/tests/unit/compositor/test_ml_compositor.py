import pytest
from plantangenet.compositor.ml_types import (
    MLCompositor,
    ClassifierCompositor,
    OnlineLearningCompositor,
    AnomalyDetectionCompositor,
    ReinforcementLearningCompositor,
    UnsupervisedCompositor,
    SequenceModelingCompositor,
    GenerativeCompositor,
    AudioSignalCompositor
)


class DummyClassifier(ClassifierCompositor):
    def fit(self, X, y=None):
        self._fitted = True

    def predict(self, X):
        return [1 for _ in X]

    def update(self, X, y=None):
        return None


def test_classifier_transform_and_compose():
    clf = DummyClassifier()
    X = [[0], [1], [2]]
    y = [0, 1, 1]
    clf.compose(X, y)
    preds = clf.transform(X)
    assert preds == [1, 1, 1]


def test_mlcompositor_transform_not_implemented():
    class Dummy(MLCompositor):
        def fit(self, X, y=None): pass
        def predict(self, X): raise NotImplementedError
        def update(self, X, y=None): pass
    d = Dummy()
    with pytest.raises(NotImplementedError):
        d.transform([1, 2, 3])


def test_online_learning_compositor_stub():
    class Dummy(OnlineLearningCompositor):
        def fit(self, X, y=None): pass
        def predict(self, X): return X
        def update(self, X, y=None): pass
    d = Dummy()
    assert d.transform([1, 2]) == [1, 2]


def test_anomaly_detection_compositor_stub():
    class Dummy(AnomalyDetectionCompositor):
        def fit(self, X, y=None): pass
        def predict(self, X): return [False for _ in X]
        def update(self, X, y=None): pass
    d = Dummy()
    assert d.transform([1, 2, 3]) == [False, False, False]


def test_unsupervised_compositor_stub():
    class Dummy(UnsupervisedCompositor):
        def fit(self, X, y=None): pass
        def predict(self, X): return [0 for _ in X]
        def update(self, X, y=None): pass
    d = Dummy()
    assert d.transform([1, 2, 3]) == [0, 0, 0]


def test_sequence_modeling_compositor_stub():
    class Dummy(SequenceModelingCompositor):
        def fit(self, X, y=None): pass
        def predict(self, X): return X[::-1]
        def update(self, X, y=None): pass
    d = Dummy()
    assert d.transform([1, 2, 3]) == [3, 2, 1]


def test_generative_compositor_generate():
    class Dummy(GenerativeCompositor):
        def fit(self, X, y=None): pass
        def predict(self, X): return X
        def update(self, X, y=None): pass
        def generate(self, context=None): return "generated"
    d = Dummy()
    assert d.generate() == "generated"


def test_audio_signal_compositor_stub():
    class Dummy(AudioSignalCompositor):
        def fit(self, X, y=None): pass
        def predict(self, X): return X
        def update(self, X, y=None): pass
    d = Dummy()
    assert d.transform([1, 2, 3]) == [1, 2, 3]


def test_reinforcement_learning_compositor_stub():
    class Dummy(ReinforcementLearningCompositor):
        def fit(self, X, y=None): pass
        def predict(self, X): return X
        def update(self, X, y=None): pass
        def act(self, state): return "action"
        def learn(self, experience): return "learned"
    d = Dummy()
    assert d.act("state") == "action"
    assert d.learn("exp") == "learned"
