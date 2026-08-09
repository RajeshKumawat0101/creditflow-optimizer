import time
import itertools
from typing import Dict, List, Set, Tuple, Optional
from models import ProblemInstance, ScheduleResult

def pure_brute_force_solve(instance: ProblemInstance, lambda_bal: float = 1.0) -> ScheduleResult:
    """
    100% Independent Naive Brute-Force Solver for Ground-Truth Verification.
    Does NOT call validator.py. Performs inline F1, F2, F3 checks and penalty calculation.
    Enumerates all K^n assignments without pruning.
    """
    start_clock = time.perf_counter()
    n, K = instance.n, instance.K
    task_map = {t.task_id: t for t in instance.tasks}

    best_schedule: Optional[Dict[int, int]] = None
    best_total_penalty = float('inf')
    best_base_penalty = float('inf')
    best_bal_penalty = float('inf')

    # Generate all candidate slot combinations in task range [l_i, u_i]
    slot_domains = [list(range(task_map[i].release_time, task_map[i].deadline + 1)) for i in range(1, n + 1)]

    for assignment in itertools.product(*slot_domains):
        schedule = {i + 1: slot for i, slot in enumerate(assignment)}
        
        # 1. Inline F3 Hard SLA Window Check
        f3_ok = True
        for tid, slot in schedule.items():
            t = task_map[tid]
            if not (t.release_time <= slot <= t.deadline):
                f3_ok = False
                break
        if not f3_ok:
            continue

        # 2. Inline F1 Conflict Exclusion Check
        f1_ok = True
        for u, v in instance.conflicts:
            if u in schedule and v in schedule:
                if schedule[u] == schedule[v]:
                    f1_ok = False
                    break
        if not f1_ok:
            continue

        # 3. Inline F2 4D Capacity Limit Check
        f2_ok = True
        usage = [[0, 0, 0, 0] for _ in range(K + 1)]
        for tid, slot in schedule.items():
            r = task_map[tid].resources
            for m in range(4):
                usage[slot][m] += r[m]

        for s in range(1, K + 1):
            cap = instance.capacities[s - 1]
            for m in range(4):
                if usage[s][m] > cap[m]:
                    f2_ok = False
                    break
            if not f2_ok:
                break
        if not f2_ok:
            continue

        # 4. Inline Objective Calculation
        p_base = sum(task_map[tid].weight * slot for tid, slot in schedule.items())
        p_bal = 0.0
        for m in range(4):
            u_m = []
            for s in range(1, K + 1):
                c_sm = instance.capacities[s - 1][m]
                u_sm = (usage[s][m] / c_sm) if c_sm > 0 else 0.0
                u_m.append(u_sm)
            avg_u = sum(u_m) / K
            p_bal += sum((val - avg_u) ** 2 for val in u_m)

        p_total = p_base + lambda_bal * p_bal

        if p_total < best_total_penalty - 1e-9:
            best_total_penalty = p_total
            best_base_penalty = p_base
            best_bal_penalty = p_bal
            best_schedule = schedule.copy()

    elapsed_ms = (time.perf_counter() - start_clock) * 1000.0

    if best_schedule is None:
        return ScheduleResult(
            status='PROVEN_INFEASIBLE',
            schedule={},
            penalty_base=float('inf'),
            penalty_bal=float('inf'),
            penalty_total=float('inf'),
            runtime_ms=elapsed_ms,
            violations=["Pure Brute Force proved instance is infeasible"]
        )

    return ScheduleResult(
        status='OPTIMAL',
        schedule=best_schedule,
        penalty_base=best_base_penalty,
        penalty_bal=best_bal_penalty,
        penalty_total=best_total_penalty,
        runtime_ms=elapsed_ms,
        violations=[]
    )
