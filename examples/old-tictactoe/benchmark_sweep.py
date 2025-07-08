import subprocess
import csv
import time

# Extended parameters to sweep
player_counts = [20000, 40000, 80000, 160000]
ref_counts = [500, 1000, 2000, 4000, 8000]
runtime = 5  # seconds per run

results = []

for players in player_counts:
    for refs in ref_counts:
        print(f"Running: players={players}, refs={refs}")
        cmd = [
            "python", "examples/tictactoe/main.py",
            f"--players={players}", f"--refs={refs}", f"--time={runtime}", "--benchmark"
        ]
        start = time.time()
        proc = subprocess.run(cmd, capture_output=True, text=True)
        end = time.time()
        output = proc.stdout
        # Parse output for stats
        lines = output.splitlines()
        agg_line = next(
            (l for l in lines if l.startswith("Total Games:")), None)
        if agg_line:
            parts = agg_line.split("|")
            games = int(parts[0].split(":")[1].strip())
            moves = int(parts[1].split(":")[1].strip())
            ttime = float(parts[2].split(":")[1].strip().replace('s', ''))
            gps = float(parts[3].split()[0])
            mps = float(parts[4].split()[0])
            results.append({
                "players": players,
                "refs": refs,
                "games": games,
                "moves": moves,
                "time": ttime,
                "games_per_sec": gps,
                "moves_per_sec": mps,
                "wall_time": end-start
            })
        else:
            results.append({
                "players": players,
                "refs": refs,
                "games": None,
                "moves": None,
                "time": None,
                "games_per_sec": None,
                "moves_per_sec": None,
                "wall_time": end-start
            })

# Write results to CSV
with open("benchmark_results.csv", "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=results[0].keys())
    writer.writeheader()
    writer.writerows(results)

print("Benchmark sweep complete. Results saved to benchmark_results.csv.")
