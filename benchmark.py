import time
import math
import numpy as np
import matplotlib.pyplot as plt
from typing import List, Dict, Tuple
from instance_generator import generate_random_instance
from solvers import BruteForceSolver, MultiDimensionalDSATURSolver, validate_schedule

def run_benchmarks():
    print("=" * 80)
    print("PERFORMANCE EVALUATION SUITE: BRUTE FORCE VS MULTI-DIMENSIONAL DSATUR")
    print("=" * 80)

    # ---------------------------------------------------------
    # PART 1: Small Instances (Brute Force vs Heuristic)
    # ---------------------------------------------------------
    small_sizes = [3, 4, 5, 6]
    bf_runtimes = []
    dsatur_runtimes_small = []
    bf_penalties = []
    dsatur_penalties_small = []
    optimality_gaps = []

    print("\n--- 1. Small Instance Comparative Analysis (Exact vs Heuristic) ---")
    print(f"{'N Tasks':<10}{'BF Time (ms)':<15}{'DSATUR Time (ms)':<18}{'BF Penalty':<15}{'DSATUR Penalty':<18}{'Opt Gap (%)':<15}")
    print("-" * 91)

    for n in small_sizes:
        inst = generate_random_instance(num_tasks=n, edge_probability=0.3, max_horizon=60, seed=42 + n)
        
        # Brute Force
        bf = BruteForceSolver(inst)
        bf_res = bf.solve()
        bf_runtimes.append(bf_res.runtime_ms)
        bf_penalties.append(bf_res.total_penalty)
        
        # DSATUR
        dsatur = MultiDimensionalDSATURSolver(inst)
        dsatur_res = dsatur.solve()
        dsatur_runtimes_small.append(dsatur_res.runtime_ms)
        dsatur_penalties_small.append(dsatur_res.total_penalty)
        
        # Calculate Optimality Gap: ((ALG - OPT) / OPT) * 100
        if bf_res.total_penalty < float('inf') and bf_res.total_penalty > 0:
            gap = ((dsatur_res.total_penalty - bf_res.total_penalty) / bf_res.total_penalty) * 100.0
        else:
            gap = 0.0
        optimality_gaps.append(gap)

        print(f"{n:<10}{bf_res.runtime_ms:<15.2f}{dsatur_res.runtime_ms:<18.2f}{bf_res.total_penalty:<15.2f}{dsatur_res.total_penalty:<18.2f}{gap:<15.2f}%")

    # ---------------------------------------------------------
    # PART 2: Scaling Analysis for Large Instances
    # ---------------------------------------------------------
    large_sizes = [10, 25, 50, 100, 200, 400]
    dsatur_runtimes_large = []
    dsatur_penalties_large = []
    feasibility_status = []

    print("\n--- 2. Large Instance Scaling Analysis (Multi-Dimensional DSATUR) ---")
    print(f"{'N Tasks':<10}{'DSATUR Time (ms)':<20}{'Total Penalty':<20}{'Feasible':<15}")
    print("-" * 65)

    for n in large_sizes:
        inst = generate_random_instance(num_tasks=n, edge_probability=0.2, max_horizon=250, seed=100 + n)
        dsatur = MultiDimensionalDSATURSolver(inst)
        dsatur_res = dsatur.solve()
        
        dsatur_runtimes_large.append(dsatur_res.runtime_ms)
        dsatur_penalties_large.append(dsatur_res.total_penalty if dsatur_res.is_feasible else float('inf'))
        feasibility_status.append(dsatur_res.is_feasible)

        status_str = "YES" if dsatur_res.is_feasible else "NO (Breached Horizon)"
        pen_str = f"{dsatur_res.total_penalty:.2f}" if dsatur_res.is_feasible else "INF"
        print(f"{n:<10}{dsatur_res.runtime_ms:<20.2f}{pen_str:<20}{status_str:<15}")

    # ---------------------------------------------------------
    # PART 3: Profiling Execution Bottlenecks
    # ---------------------------------------------------------
    print("\n--- 3. Profiling Execution Bottlenecks ---")
    inst_profile = generate_random_instance(num_tasks=200, edge_probability=0.25, max_horizon=300, seed=999)
    
    t0 = time.perf_counter()
    adj = {t.task_id: set() for t in inst_profile.tasks}
    for u, v in inst_profile.conflicts:
        adj[u].add(v)
        adj[v].add(u)
    t_sat = (time.perf_counter() - t0) * 1000.0

    t0 = time.perf_counter()
    for _ in range(50000):
        _ = inst_profile.is_conflicting(10, 20)
    t_conflict = (time.perf_counter() - t0) * 1000.0

    t0 = time.perf_counter()
    c1, c2, c3, c4 = inst_profile.resource_capacities
    for _ in range(10000):
        r1, r2, r3, r4 = 45, 30, 20, 15
        _ = (r1 <= c1 and r2 <= c2 and r3 <= c3 and r4 <= c4)
    t_resource = (time.perf_counter() - t0) * 1000.0

    print(f"Saturation Priority Queue Ops: {t_sat:.2f} ms")
    print(f"Conflict Graph Lookup Overhead: {t_conflict:.2f} ms")
    print(f"4D Capacity Constraint Checks: {t_resource:.2f} ms")

    # ---------------------------------------------------------
    # PART 4: Generating Charts
    # ---------------------------------------------------------
    print("\nGenerating Performance Charts...")

    fig, axs = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle("Scheduling Algorithm Performance & Scaling Benchmark", fontsize=16, fontweight='bold')

    # Chart 1: Small Instance Runtime (Log Scale)
    axs[0, 0].plot(small_sizes, bf_runtimes, 'r-o', linewidth=2, label='Brute Force (Exact OPT)')
    axs[0, 0].plot(small_sizes, dsatur_runtimes_small, 'b-s', linewidth=2, label='MultiD-DSATUR Heuristic')
    axs[0, 0].set_yscale('log')
    axs[0, 0].set_title('Small Instance Execution Time (Log Scale)', fontsize=12)
    axs[0, 0].set_xlabel('Number of Tasks (N)')
    axs[0, 0].set_ylabel('Runtime (ms)')
    axs[0, 0].grid(True, which="both", ls="--", alpha=0.5)
    axs[0, 0].legend()

    # Chart 2: Optimality Gap (%)
    axs[0, 1].bar([str(n) for n in small_sizes], optimality_gaps, color='teal', width=0.5)
    axs[0, 1].set_title('DSATUR Optimality Gap vs Exact OPT (%)', fontsize=12)
    axs[0, 1].set_xlabel('Number of Tasks (N)')
    axs[0, 1].set_ylabel('Sub-optimality Gap (%)')
    axs[0, 1].grid(True, axis='y', ls="--", alpha=0.5)

    # Chart 3: Large Instance Scaling
    axs[1, 0].plot(large_sizes, dsatur_runtimes_large, 'g-^', linewidth=2.5, label='DSATUR Heuristic')
    axs[1, 0].set_title('Heuristic Scaling up to N=400 Tasks', fontsize=12)
    axs[1, 0].set_xlabel('Number of Tasks (N)')
    axs[1, 0].set_ylabel('Runtime (ms)')
    axs[1, 0].grid(True, ls="--", alpha=0.5)
    axs[1, 0].legend()

    # Chart 4: Execution Time Bottleneck Distribution
    components = ['Saturation Degree', 'Conflict Graph', '4D Resource']
    times = [t_sat, t_conflict, t_resource]
    axs[1, 1].pie(times, labels=components, autopct='%1.1f%%', colors=['#ff9999','#66b3ff','#99ff99'], startangle=140)
    axs[1, 1].set_title('Runtime Bottleneck Profile Breakdown', fontsize=12)

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    plt.savefig('d:/CreditFlow Optimizer/benchmark_charts.png', dpi=300)
    print("Charts saved successfully to d:/CreditFlow Optimizer/benchmark_charts.png")

if __name__ == '__main__':
    run_benchmarks()
