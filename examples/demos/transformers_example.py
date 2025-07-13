"""
Example and proof-of-work for GPU/CPU transformers in plantangenet/compositor/gpu_transformers.py.
Demonstrates both MomentumTransformer and VectorMagnitudeTransformer with scalar and array inputs.
Also benchmarks performance for large arrays (proof of work).
"""

import numpy as np
import time
from plantangenet.compositor.gpu_transformers import HAS_CUPY, MomentumTransformer, VectorMagnitudeTransformer

print("CuPy available:" if HAS_CUPY else "Falling back to NumPy.")

# --- Demo: MomentumTransformer ---
mt = MomentumTransformer()
print("MomentumTransformer, array:", mt(
    {"mass": [1, 2, 3], "velocity": [4, 5, 6]}, None))
print("MomentumTransformer, scalar:", mt({"mass": 2, "velocity": 5}, None))

# --- Demo: VectorMagnitudeTransformer ---
vmt = VectorMagnitudeTransformer("x", "y", "z")
print("VectorMagnitudeTransformer, array:", vmt(
    {"x": [3, 0], "y": [4, 0], "z": [0, 5]}, None))
print("VectorMagnitudeTransformer, scalar:",
      vmt({"x": 3, "y": 4, "z": 0}, None))

# --- Proof of Work: Large Array Benchmark ---
N = 10**6
mass = np.ones(N)
velocity = np.arange(N)
x = np.random.randn(N)
y = np.random.randn(N)
z = np.random.randn(N)

print("\n--- Proof of Work: Large Array Benchmark ---")
start = time.time()
mt_result = mt({"mass": mass, "velocity": velocity}, None)
print(
    f"MomentumTransformer (N={N}): {time.time() - start:.4f}s, sample: {mt_result['momentum'][:5]}")

start = time.time()
vmt_result = vmt({"x": x, "y": y, "z": z}, None)
print(
    f"VectorMagnitudeTransformer (N={N}): {time.time() - start:.4f}s, sample: {vmt_result['magnitude'][:5]}")
