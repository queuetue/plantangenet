"""
examples/nbody_benchmark.py
A simple N-body simulation and benchmark for Python CPU-bound performance.

This script simulates N particles interacting via gravity in 2D, using O(N^2) brute-force computation.
It reports steps/sec and interactions/sec, and can be used to benchmark Python's computational throughput.
"""
import cupy as cp
import math
import random
import time
import argparse


def nbody_step(positions, velocities, masses, dt=0.01, G=1.0):
    N = len(positions)
    forces = [[0.0, 0.0] for _ in range(N)]
    # Compute pairwise forces
    for i in range(N):
        for j in range(i + 1, N):
            dx = positions[j][0] - positions[i][0]
            dy = positions[j][1] - positions[i][1]
            dist_sq = dx * dx + dy * dy + 1e-10  # avoid div by zero
            dist = math.sqrt(dist_sq)
            force = G * masses[i] * masses[j] / dist_sq
            fx = force * dx / dist
            fy = force * dy / dist
            forces[i][0] += fx
            forces[i][1] += fy
            forces[j][0] -= fx
            forces[j][1] -= fy
    # Update velocities and positions
    for i in range(N):
        velocities[i][0] += forces[i][0] / masses[i] * dt
        velocities[i][1] += forces[i][1] / masses[i] * dt
        positions[i][0] += velocities[i][0] * dt
        positions[i][1] += velocities[i][1] * dt


def run_nbody_benchmark(N=100, steps=100, dt=0.01, seed=None):
    if seed is not None:
        random.seed(seed)
    positions = [[random.uniform(-1, 1), random.uniform(-1, 1)]
                 for _ in range(N)]
    velocities = [[0.0, 0.0] for _ in range(N)]
    masses = [random.uniform(0.5, 2.0) for _ in range(N)]
    start = time.time()
    for step in range(steps):
        nbody_step(positions, velocities, masses, dt)
    elapsed = time.time() - start
    print(f"N={N}, steps={steps}, time={elapsed:.3f}s, steps/sec={steps/elapsed:.2f}, interactions/sec={steps*N*N/elapsed:.2f}")


def main():
    parser = argparse.ArgumentParser(
        description="N-body simulation benchmark.")
    parser.add_argument("-n", "--num-bodies", type=int,
                        default=100, help="Number of bodies (particles)")
    parser.add_argument("-s", "--steps", type=int,
                        default=100, help="Number of simulation steps")
    parser.add_argument("-d", "--dt", type=float,
                        default=0.01, help="Timestep size")
    parser.add_argument("--seed", type=int, default=None, help="Random seed")
    args = parser.parse_args()
    run_nbody_benchmark(N=args.num_bodies, steps=args.steps,
                        dt=args.dt, seed=args.seed)


if __name__ == "__main__":
    main()
