import time
import random
import math
from typing import Dict, List, Set, Tuple, Optional
from models import ProblemInstance, ScheduleResult
from validator import validate_schedule, compute_penalty

def rsp_rrs_solve(
    inst: ProblemInstance, 
    lambda_bal: float = 1.0, 
    max_lns_iters: int = 100, 
    seed: int = 42
) -> ScheduleResult:
    r"""
    Resource-SLA Priority-Heuristic with Focused Ruin-Recreate and Swap Search (RSP-RRS).
    Constructive phase complexity: O(n^2 K \Delta + n K^2 d).
    Swap search complexity: O(I_swap * (n^3 + n^2 \Delta + n^2 K d)).
    Does NOT claim guaranteed global feasibility.
    """
    start_clock = time.perf_counter()
    rng = random.Random(seed)
    n, K = inst.n, inst.K
    task_map = {t.task_id: t for t in inst.tasks}

    # Pre-build adjacency representation
    adj: Dict[int, Set[int]] = {i: set() for i in range(1, n + 1)}
    for u, v in inst.conflicts:
        if u in adj and v in adj:
            adj[u].add(v)
            adj[v].add(u)

    # Global State Matrix: usage[s][m] for s in 1...K, m in 0...3
    schedule: Dict[int, int] = {}
    usage = [[0, 0, 0, 0] for _ in range(K + 1)]
    current_base_penalty = 0.0

    # --- Incremental State Operations ---
    def is_f1_valid(tid: int, slot: int) -> bool:
        return not any(schedule.get(nbr) == slot for nbr in adj[tid])

    def is_f2_valid(tid: int, slot: int) -> bool:
        r = task_map[tid].resources
        cap = inst.capacities[slot - 1]
        return all(usage[slot][m] + r[m] <= cap[m] for m in range(4))

    def assign_task(tid: int, slot: int):
        nonlocal current_base_penalty
        schedule[tid] = slot
        current_base_penalty += task_map[tid].weight * slot
        r = task_map[tid].resources
        for m in range(4):
            usage[slot][m] += r[m]

    def unassign_task(tid: int):
        nonlocal current_base_penalty
        slot = schedule[tid]
        current_base_penalty -= task_map[tid].weight * slot
        r = task_map[tid].resources
        for m in range(4):
            usage[slot][m] -= r[m]
        del schedule[tid]

    def compute_domain_size(tid: int) -> int:
        t = task_map[tid]
        return sum(1 for s in range(t.release_time, t.deadline + 1) if is_f1_valid(tid, s) and is_f2_valid(tid, s))

    def evaluate_candidate_slot_objective(tid: int, slot: int) -> float:
        """
        100% Objective-Aware Candidate Slot Evaluation in O(K d) time.
        Uses incremental current_base_penalty and computes K-slot normalized utilization variance.
        """
        assign_task(tid, slot)
        
        p_base = current_base_penalty  # O(1)
        p_bal = 0.0
        if lambda_bal > 0.0:
            for m in range(4):
                u_m = []
                for s_idx in range(1, K + 1):
                    c_sm = inst.capacities[s_idx - 1][m]
                    u_sm = (usage[s_idx][m] / c_sm) if c_sm > 0 else 0.0
                    u_m.append(u_sm)
                avg_u = sum(u_m) / K
                p_bal += sum((u_sm - avg_u) ** 2 for u_sm in u_m)

        cost = p_base + lambda_bal * p_bal
        unassign_task(tid)
        return cost

    def identify_causal_blockers(failed_tid: int) -> Set[int]:
        """
        Greedily Identified Capacity & Conflict Blockers.
        Identifies assigned tasks causing F1 conflict or F2 capacity deficit for failed_tid across candidate slots [l_k, u_k].
        """
        t_failed = task_map[failed_tid]
        blockers = set()

        for s in range(t_failed.release_time, t_failed.deadline + 1):
            # 1. F1 Conflict Blockers in slot s
            for nbr in adj[failed_tid]:
                if nbr in schedule and schedule[nbr] == s:
                    blockers.add(nbr)

            # 2. F2 Capacity Blockers in slot s
            if not is_f2_valid(failed_tid, s):
                r_failed = t_failed.resources
                cap = inst.capacities[s - 1]
                
                for m in range(4):
                    deficit = (usage[s][m] + r_failed[m]) - cap[m]
                    if deficit > 0:
                        occupying = [tid for tid, assigned_s in schedule.items() if assigned_s == s and task_map[tid].resources[m] > 0]
                        occupying.sort(key=lambda tid: task_map[tid].resources[m], reverse=True)
                        
                        accumulated = 0
                        for tid in occupying:
                            blockers.add(tid)
                            accumulated += task_map[tid].resources[m]
                            if accumulated >= deficit:
                                break

        return blockers

    # --- PHASE 1: Constructive Assignment (MRV Priority + Objective-Aware Candidate Slot Selection) ---
    unassigned = set(range(1, n + 1))

    while unassigned:
        best_tid = min(
            unassigned,
            key=lambda tid: (
                compute_domain_size(tid),
                -len(adj[tid]),
                -task_map[tid].weight,
                tid
            )
        )

        t = task_map[best_tid]
        best_slot = -1
        min_candidate_cost = float('inf')

        for s in range(t.release_time, t.deadline + 1):
            if is_f1_valid(best_tid, s) and is_f2_valid(best_tid, s):
                cost = evaluate_candidate_slot_objective(best_tid, s)
                if cost < min_candidate_cost:
                    min_candidate_cost = cost
                    best_slot = s

        if best_slot != -1:
            assign_task(best_tid, best_slot)
            unassigned.remove(best_tid)
        else:
            break

    # --- PHASE 2: Focused Ruin & Recreate LNS Repair ---
    if unassigned:
        for _ in range(max_lns_iters):
            failed_tid = next(iter(unassigned))

            blockers = identify_causal_blockers(failed_tid)

            # Ruin target: Blockers + max(1, ceil(0.15 * n)) random sample of assigned tasks
            num_sample = max(1, math.ceil(0.15 * n))
            assigned_keys = list(schedule.keys())
            random_sample = set(rng.sample(assigned_keys, min(len(assigned_keys), num_sample)))
            ruin_targets = blockers.union(random_sample)

            for tid in ruin_targets:
                if tid in schedule:
                    unassign_task(tid)
                    unassigned.add(tid)

            reinsert_list = sorted(
                list(unassigned),
                key=lambda tid: (
                    compute_domain_size(tid),
                    -len(adj[tid]),
                    -task_map[tid].weight,
                    tid
                )
            )

            for tid in reinsert_list:
                t_re = task_map[tid]
                best_slot = -1
                min_cost = float('inf')

                for s in range(t_re.release_time, t_re.deadline + 1):
                    if is_f1_valid(tid, s) and is_f2_valid(tid, s):
                        cost = evaluate_candidate_slot_objective(tid, s)
                        if cost < min_cost:
                            min_cost = cost
                            best_slot = s

                if best_slot != -1:
                    assign_task(tid, best_slot)
                    unassigned.remove(tid)

            if not unassigned:
                break

    # --- PHASE 3: Strictly Improving Pairwise Swap Local Search ---
    if not unassigned:
        p_base, p_bal, current_cost = compute_penalty(inst, schedule, lambda_bal)
        task_ids = list(range(1, n + 1))
        
        improved = True
        while improved:
            improved = False
            for i in range(len(task_ids)):
                for j in range(i + 1, len(task_ids)):
                    u, v = task_ids[i], task_ids[j]
                    su, sv = schedule[u], schedule[v]
                    if su != sv:
                        tu, tv = task_map[u], task_map[v]
                        if (tu.release_time <= sv <= tu.deadline) and (tv.release_time <= su <= tv.deadline):
                            unassign_task(u)
                            unassign_task(v)

                            if is_f1_valid(u, sv) and is_f2_valid(u, sv) and is_f1_valid(v, su) and is_f2_valid(v, su):
                                assign_task(u, sv)
                                assign_task(v, su)

                                candidate_base, candidate_bal, candidate_cost = compute_penalty(inst, schedule, lambda_bal)
                                # Floating-point safe strict improvement check
                                if candidate_cost < current_cost - 1e-9:
                                    current_cost = candidate_cost
                                    improved = True
                                    break
                                else:
                                    unassign_task(u)
                                    unassign_task(v)
                                    assign_task(u, su)
                                    assign_task(v, sv)
                            else:
                                assign_task(u, su)
                                assign_task(v, sv)
                if improved:
                    break

    elapsed_ms = (time.perf_counter() - start_clock) * 1000.0

    if unassigned:
        return ScheduleResult(
            status='HEURISTIC_FAILED',
            schedule=schedule,
            penalty_base=float('inf'),
            penalty_bal=float('inf'),
            penalty_total=float('inf'),
            runtime_ms=elapsed_ms,
            violations=[f"Unassigned tasks remaining: {len(unassigned)}"]
        )

    p_base, p_bal, p_total = compute_penalty(inst, schedule, lambda_bal)
    val = validate_schedule(inst, schedule)

    return ScheduleResult(
        status='FEASIBLE',
        schedule=schedule,
        penalty_base=p_base,
        penalty_bal=p_bal,
        penalty_total=p_total,
        runtime_ms=elapsed_ms,
        violations=val["violations"]
    )
