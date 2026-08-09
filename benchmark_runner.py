import time
import math
import json
from typing import List, Dict
import matplotlib.pyplot as plt

from models import Task, ProblemInstance
from generator import generate_instance
from solvers.rsp_rrs import rsp_rrs_solve
from solvers.da_bnb import da_bnb_exact_solve
from solvers.pure_brute_force import pure_brute_force_solve

def run_benchmarks():
    print("=" * 110)
    print("EXECUTABLE BENCHMARK RUNNER: PRESCRIBED SCOREME ASSIGNMENT BENCHMARK SUITE")
    print("=" * 110)

    # The 9 Prescribed Assignment Benchmark Configurations
    prescribed_cases = [
        {"category": "Small",  "n": 8,   "K": 3,  "density": 0.30, "seed": 1},
        {"category": "Small",  "n": 10,  "K": 4,  "density": 0.40, "seed": 2},
        {"category": "Small",  "n": 12,  "K": 4,  "density": 0.50, "seed": 3},
        {"category": "Medium", "n": 50,  "K": 8,  "density": 0.25, "seed": 10},
        {"category": "Medium", "n": 100, "K": 10, "density": 0.30, "seed": 11},
        {"category": "Medium", "n": 150, "K": 12, "density": 0.35, "seed": 12},
        {"category": "Stress", "n": 200, "K": 15, "density": 0.40, "seed": 20},
        {"category": "Stress", "n": 200, "K": 5,  "density": 0.60, "seed": 21},
        {"category": "Stress", "n": 200, "K": 20, "density": 0.10, "seed": 22},
    ]

    benchmark_results = []
    
    print("\n--- 1. Executing 9 Prescribed Benchmark Cases ---")
    print(f"{'Cat':<8}{'N':<5}{'K':<5}{'Density':<9}{'Seed':<6}{'Exact Status':<18}{'P_OPT':<12}{'RSP-RRS Status':<18}{'P_heur':<12}{'Emp Ratio':<10}{'Runtime(ms)':<12}")
    print("-" * 125)

    for cfg in prescribed_cases:
        n, K, density, seed = cfg["n"], cfg["K"], cfg["density"], cfg["seed"]
        inst = generate_instance(num_tasks=n, num_slots=K, edge_probability=density, seed=seed)

        # Run exact solver on small instances (n <= 12) with a reasonable timeout/limit check
        if n <= 12:
            exact_res = da_bnb_exact_solve(inst, lambda_bal=1.0)
            exact_status = exact_res.status
            p_opt = exact_res.penalty_total if exact_status == 'OPTIMAL' else float('inf')
        else:
            exact_status = "N/A (Large)"
            p_opt = float('nan')

        # Run RSP-RRS Heuristic Solver
        heur_res = rsp_rrs_solve(inst, lambda_bal=1.0, max_lns_iters=100, seed=seed)
        p_heur = heur_res.penalty_total if heur_res.status == 'FEASIBLE' else float('inf')

        # Calculate empirical ratio
        if not math.isnan(p_opt) and exact_status == 'OPTIMAL' and heur_res.status == 'FEASIBLE':
            ratio = p_heur / p_opt
            ratio_str = f"{ratio:.4f}"
        else:
            ratio = float('nan')
            ratio_str = "N/A"

        p_opt_str = f"{p_opt:.4f}" if not math.isnan(p_opt) and exact_status == 'OPTIMAL' else ("INF" if exact_status == 'PROVEN_INFEASIBLE' else "N/A")
        p_heur_str = f"{p_heur:.4f}" if heur_res.status == 'FEASIBLE' else "FAILED"

        print(f"{cfg['category']:<8}{n:<5}{K:<5}{density:<9.2f}{seed:<6}{exact_status:<18}{p_opt_str:<12}{heur_res.status:<18}{p_heur_str:<12}{ratio_str:<10}{heur_res.runtime_ms:<12.2f}")

        benchmark_results.append({
            "category": cfg["category"],
            "n": n,
            "K": K,
            "density": density,
            "seed": seed,
            "exact_status": exact_status,
            "p_opt": p_opt if not math.isnan(p_opt) else None,
            "heur_status": heur_res.status,
            "p_heur": p_heur if heur_res.status == 'FEASIBLE' else None,
            "empirical_ratio": ratio if not math.isnan(ratio) else None,
            "runtime_ms": round(heur_res.runtime_ms, 2)
        })

    # Save benchmark results to JSON
    with open("prescribed_benchmarks.json", "w") as f:
        json.dump(benchmark_results, f, indent=2)
    print("\nSaved benchmark metrics to prescribed_benchmarks.json")

    # Generate Required Plots (penalty_vs_n.png and runtime_vs_n.png)
    feasible_results = [r for r in benchmark_results if r["heur_status"] == 'FEASIBLE']
    n_vals = [r["n"] for r in feasible_results]
    penalties = [r["p_heur"] for r in feasible_results]
    runtimes = [r["runtime_ms"] for r in feasible_results]

    # Chart 1: Penalty vs N
    plt.figure(figsize=(8, 5))
    plt.plot(n_vals, penalties, marker='o', color='b', linestyle='-', linewidth=2)
    plt.title("RSP-RRS Total Penalty vs Number of Tasks (N)")
    plt.xlabel("Number of Tasks (N)")
    plt.ylabel("Total Penalty P_total")
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.tight_layout()
    plt.savefig("penalty_vs_n.png")
    plt.close()

    # Chart 2: Runtime vs N
    plt.figure(figsize=(8, 5))
    plt.plot(n_vals, runtimes, marker='s', color='r', linestyle='-', linewidth=2)
    plt.title("RSP-RRS Runtime (ms) vs Number of Tasks (N)")
    plt.xlabel("Number of Tasks (N)")
    plt.ylabel("Execution Time (ms)")
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.tight_layout()
    plt.savefig("runtime_vs_n.png")
    plt.close()

    print("Generated penalty_vs_n.png and runtime_vs_n.png charts.")

    # 2. Lambda Sensitivity Experiment (Deliberate Trade-off Demonstration)
    print("\n--- 2. Lambda Sensitivity Experiment (Deliberate Trade-off Demonstration) ---")
    print(f"{'Lambda':<10}{'P_base':<15}{'P_bal':<15}{'P_total':<15}{'Task 2 Slot':<15}{'Status':<15}")
    print("-" * 85)

    tasks_sens = [
        Task(1, 1, 1, 1, 100.0, (5, 0, 0, 0)),
        Task(2, 1, 1, 2, 2.0, (5, 0, 0, 0))
    ]
    inst_sens = ProblemInstance(2, 2, tasks_sens, set(), [(10, 10, 10, 10), (10, 10, 10, 10)])
    lambdas = [0.0, 0.01, 0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 50.0, 100.0]

    for l_val in lambdas:
        res = rsp_rrs_solve(inst_sens, lambda_bal=l_val, max_lns_iters=50, seed=42)
        slot_t2 = res.schedule.get(2, -1)
        p_base_str = f"{res.penalty_base:.2f}"
        p_bal_str = f"{res.penalty_bal:.4f}"
        p_total_str = f"{res.penalty_total:.4f}"
        print(f"{l_val:<10.2f}{p_base_str:<15}{p_bal_str:<15}{p_total_str:<15}{slot_t2:<15}{res.status:<15}")

if __name__ == '__main__':
    run_benchmarks()
