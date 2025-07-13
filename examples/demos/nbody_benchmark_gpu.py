"""
examples/nbody_benchmark_gpu.py
A simple N-body simulation and benchmark for Python using GPU acceleration (CuPy).

This script simulates N particles interacting via gravity in 2D, using O(N^2) brute-force computation on the GPU.
It reports steps/sec and interactions/sec, and can be used to benchmark GPU computational throughput.

Requires: cupy (pip install cupy)
"""
import cupy as cp
import time
import argparse


def nbody_step_gpu(positions, velocities, masses, dt=0.01, G=1.0):
    N = positions.shape[0]
    # Compute pairwise differences
    dx = positions[:, 0][cp.newaxis, :] - positions[:, 0][:, cp.newaxis]
    dy = positions[:, 1][cp.newaxis, :] - positions[:, 1][:, cp.newaxis]
    dist_sq = dx ** 2 + dy ** 2 + 1e-10  # avoid div by zero
    inv_dist = 1.0 / cp.sqrt(dist_sq)
    inv_dist3 = inv_dist / dist_sq
    # Compute force magnitudes
    m_prod = masses[cp.newaxis, :] * masses[:, cp.newaxis]
    force_mag = G * m_prod * inv_dist3
    # Zero out self-force
    force_mag *= 1 - cp.eye(N, dtype=cp.float32)
    # Net force on each particle
    fx = cp.sum(force_mag * dx, axis=1)
    fy = cp.sum(force_mag * dy, axis=1)
    # Update velocities and positions
    velocities[:, 0] += fx / masses * dt
    velocities[:, 1] += fy / masses * dt
    positions[:, 0] += velocities[:, 0] * dt
    positions[:, 1] += velocities[:, 1] * dt


def run_nbody_benchmark_gpu(N=100, steps=100, dt=0.01, seed=None):
    if seed is not None:
        cp.random.seed(seed)
    positions = cp.random.uniform(-1, 1, (N, 2)).astype(cp.float32)
    velocities = cp.zeros((N, 2), dtype=cp.float32)
    masses = cp.random.uniform(0.5, 2.0, N).astype(cp.float32)
    cp.cuda.Stream.null.synchronize()  # Ensure GPU is ready
    start = time.time()
    for step in range(steps):
        nbody_step_gpu(positions, velocities, masses, dt)
    cp.cuda.Stream.null.synchronize()  # Wait for GPU to finish
    elapsed = time.time() - start
    print(f"[GPU] N={N}, steps={steps}, time={elapsed:.3f}s, steps/sec={steps/elapsed:.2f}, interactions/sec={steps*N*N/elapsed:.2f}")


def main():
    parser = argparse.ArgumentParser(
        description="N-body simulation GPU benchmark (CuPy).")
    parser.add_argument("-n", "--num-bodies", type=int,
                        default=100, help="Number of bodies (particles)")
    parser.add_argument("-s", "--steps", type=int,
                        default=100, help="Number of simulation steps")
    parser.add_argument("-d", "--dt", type=float,
                        default=0.01, help="Timestep size")
    parser.add_argument("--seed", type=int, default=None, help="Random seed")
    args = parser.parse_args()
    run_nbody_benchmark_gpu(
        N=args.num_bodies, steps=args.steps, dt=args.dt, seed=args.seed)


if __name__ == "__main__":
    main()
