import cupy as cp
import random
import time
import argparse

from plantangenet.compositor.transformers import Transformer


class NBodyStepTransformer(Transformer):
    def __init__(self, dt=0.01, G=1.0):
        self.dt = dt
        self.G = G

    def __call__(self, data, frame):
        positions = cp.array(data["positions"], dtype=cp.float32)
        velocities = cp.array(data["velocities"], dtype=cp.float32)
        masses = cp.array(data["masses"], dtype=cp.float32)

        nbody_step_gpu(positions, velocities, masses, self.dt, self.G)

        data["positions"] = cp.asnumpy(positions).tolist()
        data["velocities"] = cp.asnumpy(velocities).tolist()
        return data


def nbody_step_gpu(positions, velocities, masses, dt=0.01, G=1.0):
    N = positions.shape[0]
    forces = cp.zeros((N, 2), dtype=cp.float32)
    for i in range(N):
        for j in range(i + 1, N):
            dx = positions[j][0] - positions[i][0]
            dy = positions[j][1] - positions[i][1]
            dist_sq = dx * dx + dy * dy + 1e-10
            dist = cp.sqrt(dist_sq)
            force = G * masses[i] * masses[j] / dist_sq
            fx = force * dx / dist
            fy = force * dy / dist
            forces[i][0] += fx
            forces[i][1] += fy
            forces[j][0] -= fx
            forces[j][1] -= fy
    velocities += forces / masses[:, cp.newaxis] * dt
    positions += velocities * dt


def run_nbody_benchmark(N=100, steps=100, dt=0.01, seed=None):
    if seed is not None:
        random.seed(seed)
    positions = [[random.uniform(-1, 1), random.uniform(-1, 1)]
                 for _ in range(N)]
    velocities = [[0.0, 0.0] for _ in range(N)]
    masses = [random.uniform(0.5, 2.0) for _ in range(N)]
    buffer = {"positions": positions,
              "velocities": velocities, "masses": masses}

    transformer = NBodyStepTransformer(dt=dt, G=1.0)

    cp.cuda.Stream.null.synchronize()
    start = time.time()
    for step in range(steps):
        buffer = transformer(buffer, frame=None)
    cp.cuda.Stream.null.synchronize()
    elapsed = time.time() - start

    print(f"[GPU] N={N}, steps={steps}, time={elapsed:.3f}s, steps/sec={steps/elapsed:.2f}, interactions/sec={steps*N*N/elapsed:.2f}")


def main():
    parser = argparse.ArgumentParser(description="N-body GPU benchmark.")
    parser.add_argument("-n", "--num-bodies", type=int, default=100)
    parser.add_argument("-s", "--steps", type=int, default=100)
    parser.add_argument("-d", "--dt", type=float, default=0.01)
    parser.add_argument("--seed", type=int, default=None)
    args = parser.parse_args()
    run_nbody_benchmark(N=args.num_bodies, steps=args.steps,
                        dt=args.dt, seed=args.seed)


if __name__ == "__main__":
    main()
