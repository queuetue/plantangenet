"""
GPU-accelerated transformers with graceful fallback to CPU (NumPy).
Provides educational, robust examples for ML/data pipelines and GPU/CPU switching.
"""

# GPU-accelerated transformers with graceful fallback to CPU
import warnings

try:
    import cupy as cp
    HAS_CUPY = True
except Exception as e:
    # Any import error (including CUDA issues) falls back to numpy
    try:
        import numpy as np
        cp = np  # type: ignore
        HAS_CUPY = False
        warnings.warn(
            f"CuPy not available, falling back to NumPy: {e}", UserWarning)
    except ImportError:
        raise ImportError(
            "Neither CuPy nor NumPy available for array operations")

from .transformers import Transformer
from typing import Dict, Any, Optional, Union


class MomentumTransformer(Transformer):
    """
    GPU-accelerated transformer that computes momentum = mass * velocity.
    Handles scalars, lists, tuples, and NumPy/CuPy arrays.
    Always outputs Python-native types (float or list of floats).

    Usage:
        data = {"mass": [1, 2, 3], "velocity": [4, 5, 6]}
        out = MomentumTransformer()(data, None)
        # out["momentum"] is [4.0, 10.0, 18.0]
    """

    def __call__(self, data: Dict[str, Any], frame: Any) -> Dict[str, Any]:
        mass = data.get("mass")
        velocity = data.get("velocity")

        if mass is None or velocity is None:
            warnings.warn(
                "MomentumTransformer: 'mass' or 'velocity' missing; skipping.", UserWarning)
            return data

        # Accept lists, tuples, or arrays
        def is_array(x): return isinstance(x, (list, tuple)) or (
            hasattr(x, 'shape') and hasattr(x, '__getitem__'))

        if is_array(mass) and is_array(velocity):
            mass_array = cp.array(mass)
            velocity_array = cp.array(velocity)
            if mass_array.shape != velocity_array.shape:
                warnings.warn(
                    f"MomentumTransformer: shape mismatch {mass_array.shape} vs {velocity_array.shape}; skipping.", UserWarning)
                return data
            momentum_array = mass_array * velocity_array
            # Always output as Python list
            if HAS_CUPY:
                data["momentum"] = cp.asnumpy(
                    momentum_array).tolist()  # type: ignore
            else:
                data["momentum"] = momentum_array.tolist()
        else:
            # Scalar case
            try:
                data["momentum"] = float(mass) * float(velocity)
            except Exception as e:
                warnings.warn(
                    f"MomentumTransformer: could not compute scalar momentum: {e}", UserWarning)
        return data


class VectorMagnitudeTransformer(Transformer):
    """
    GPU-accelerated transformer that computes vector magnitude from x, y, z components.
    Handles scalars, lists, tuples, and arrays. Always outputs float or list of floats.

    Usage:
        data = {"x": [3, 0], "y": [4, 0]}
        out = VectorMagnitudeTransformer("x", "y")(data, None)
        # out["magnitude"] is [5.0, 0.0]
    """

    def __init__(self, x_field: str, y_field: str, z_field: Optional[str] = None, output_field: str = "magnitude"):
        self.x_field = x_field
        self.y_field = y_field
        self.z_field = z_field
        self.output_field = output_field

    def __call__(self, data: Dict[str, Any], frame: Any) -> Dict[str, Any]:
        x = data.get(self.x_field)
        y = data.get(self.y_field)
        z = data.get(self.z_field, 0) if self.z_field else 0

        if x is None or y is None:
            warnings.warn(
                f"VectorMagnitudeTransformer: '{self.x_field}' or '{self.y_field}' missing; skipping.", UserWarning)
            return data

        def is_array(v): return isinstance(v, (list, tuple)) or (
            hasattr(v, 'shape') and hasattr(v, '__getitem__'))

        if is_array(x) and is_array(y):
            x_gpu = cp.array(x)
            y_gpu = cp.array(y)
            z_gpu = cp.array(z) if is_array(z) else cp.full_like(x_gpu, z)
            if x_gpu.shape != y_gpu.shape or x_gpu.shape != z_gpu.shape:
                warnings.warn(
                    f"VectorMagnitudeTransformer: shape mismatch in inputs; skipping.", UserWarning)
                return data
            magnitude_gpu = cp.sqrt(x_gpu**2 + y_gpu**2 + z_gpu**2)
            if HAS_CUPY:
                data[self.output_field] = cp.asnumpy(
                    magnitude_gpu).tolist()  # type: ignore
            else:
                data[self.output_field] = magnitude_gpu.tolist()
        else:
            try:
                data[self.output_field] = float(
                    (float(x)**2 + float(y)**2 + float(z)**2)**0.5)
            except Exception as e:
                warnings.warn(
                    f"VectorMagnitudeTransformer: could not compute scalar magnitude: {e}", UserWarning)
        return data
