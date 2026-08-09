import time
import math
from typing import List, Dict
from models import Task, ProblemInstance
from generator import generate_instance
from solvers.rsp_rrs import rsp_rrs_solve
from solvers.da_bnb import da_bnb_exact_solve
from solvers.pure_brute_force import pure_brute_force_solve

def run_benchmarks():
    print("=" * 95)
    print("EXECUTABLE BENCHMARK RUNNER: RSP-RRS HEURISTIC VS DA-BNB EXACT SOLVER")
    print("=" * 95)

    # 1. Exact Comparison on Small Instances (Pure Brute-Force vs DA-BnB vs RSP-RRS)
    small_n = [4, 5, 6]
    print("\n--- 1. Small Instance Ground-Truth Evaluation (Pure BF vs DA-BnB vs RSP-RRS) ---")
    print(f"{'N':<5}{'K':<5}{'BF Status':<15}{'BnB Status':<18}{'P_base':<12}{'P_bal':<12}{'P_total(OPT)':<15}{'P_heur':<12}{'Abs Gap':<12}{'Ratio':<10}")
    print("-" * 120)

    for n in small_n:
        inst = generate_instance(num_tasks=n, num_slots=3, edge_probability=0.2, max_demand_ratio=0.3, seed=100 + n)
        
        bf_res = pure_brute_force_solve(inst, lambda_bal=1.0)
        bnb_res = da_bnb_exact_solve(inst, lambda_bal=1.0)
        heur_res = rsp_rrs_solve(inst, lambda_bal=1.0, max_lns_iters=100, seed=100 + n)

        if bnb_res.status == 'OPTIMAL' and heur_res.status == 'FEASIBLE':
            abs_gap = heur_res.penalty_total - bnb_res.penalty_total
            ratio_str = f"{heur_res.penalty_total / bnb_res.penalty_total:.4f}" if bnb_res.penalty_total > 0 else "1.0000"
        else:
            abs_gap = float('nan')
            ratio_str = "N/A"

        p_base_str = f"{bnb_res.penalty_base:.2f}" if bnb_res.status == 'OPTIMAL' else "INF"
        p_bal_str = f"{bnb_res.penalty_bal:.4f}" if bnb_res.status == 'OPTIMAL' else "INF"
        p_opt_str = f"{bnb_res.penalty_total:.4f}" if bnb_res.status == 'OPTIMAL' else "INF"
        p_heur_str = f"{heur_res.penalty_total:.4f}" if heur_res.status == 'FEASIBLE' else "FAILED"
        gap_str = f"{abs_gap:.4f}" if not math.isnan(abs_gap) else "N/A"

        print(f"{n:<5}{inst.K:<5}{bf_res.status:<15}{bnb_res.status:<18}{p_base_str:<12}{p_bal_str:<12}{p_opt_str:<15}{p_heur_str:<12}{gap_str:<12}{ratio_str:<10}")

    # 2. Large Instance Scaling Benchmark
    large_n = [10, 25, 50, 100, 200]
    print("\n--- 2. Large Instance Scaling Benchmark (RSP-RRS Heuristic) ---")
    print(f"{'N':<5}{'K':<5}{'Status':<18}{'P_base':<15}{'P_bal':<15}{'P_total':<15}{'Runtime (ms)':<15}")
    print("-" * 80)

    for n in large_n:
        k_slots = max(5, n // 3)
        inst = generate_instance(num_tasks=n, num_slots=k_slots, edge_probability=0.1, max_demand_ratio=0.25, seed=200 + n)
        heur_res = rsp_rrs_solve(inst, lambda_bal=1.0, max_lns_iters=100, seed=200 + n)

        p_base_str = f"{heur_res.penalty_base:.2f}" if heur_res.status == 'FEASIBLE' else "N/A"
        p_bal_str = f"{heur_res.penalty_bal:.4f}" if heur_res.status == 'FEASIBLE' else "N/A"
        p_total_str = f"{heur_res.penalty_total:.4f}" if heur_res.status == 'FEASIBLE' else "FAILED"

        print(f"{n:<5}{inst.K:<5}{heur_res.status:<18}{p_base_str:<15}{p_bal_str:<15}{p_total_str:<15}{heur_res.runtime_ms:<15.2f}")

    # 3. Lambda Sensitivity Demonstration Instance
    print("\n--- 3. Lambda Sensitivity Experiment (Deliberate Trade-off Demonstration) ---")
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
