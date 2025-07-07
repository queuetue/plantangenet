from abc import ABC, abstractmethod
from plantangenet.compositor.base import BaseCompositor


class MLCompositor(BaseCompositor):
    """Base class for all ML compositors."""
    @abstractmethod
    def fit(self, X, y=None):
        pass

    @abstractmethod
    def predict(self, X):
        pass

    @abstractmethod
    def update(self, X, y=None):
        """For online or continual learning."""
        pass

    def transform(self, data, **kwargs):
        """Default transform: apply predict. Subclasses can override."""
        return self.predict(data)

    def compose(self, *args, **kwargs):
        """Default compose: fit and return self. Subclasses can override."""
        if args:
            self.fit(*args, **kwargs)
        return self


class ClassifierCompositor(MLCompositor):
    """Handles classification, regression, ranking, and recommendation."""
    pass


class OnlineLearningCompositor(MLCompositor):
    """Handles online/continual learning and streaming anomaly detection."""
    pass


class AnomalyDetectionCompositor(MLCompositor):
    """Handles outlier and anomaly detection."""
    pass


class ReinforcementLearningCompositor(MLCompositor):
    """Handles RL, imitation learning, and co-creative systems."""
    @abstractmethod
    def act(self, state):
        pass

    @abstractmethod
    def learn(self, experience):
        pass


class UnsupervisedCompositor(MLCompositor):
    """Handles clustering, dimensionality reduction, and community detection."""
    pass


class SequenceModelingCompositor(MLCompositor):
    """Handles sequence models, time-series, alignment, and attention."""
    pass


class GenerativeCompositor(MLCompositor):
    """Handles generative models, data augmentation, and style transfer."""
    @abstractmethod
    def generate(self, context=None):
        pass


class AudioSignalCompositor(MLCompositor):
    """Handles audio signal processing and real-time feedback."""
    pass
