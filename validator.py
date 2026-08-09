from typing import Dict, Tuple, List
from models import ProblemInstance

def validate_schedule(instance: ProblemInstance, schedule: Dict[int, int]) -> Dict:
    """
    Independent Feasibility Validator.
    Verifies F1 (Conflicts), F2 (4D Capacity), F3 (SLA Windows).
    Returns a diagnostic dictionary. Does NOT rely on internal solver state.
    """
    violations = []
    task_map = {t.task_id: t for t in instance.tasks}

    # 1. Check complete assignment
    if len(schedule) != instance.n:
        violations.append(f"Incomplete assignment: {len(schedule)}/{instance.n} tasks assigned.")

    # 2. Check F3 Hard SLA Window
    for tid, slot in schedule.items():
        if tid in task_map:
            t = task_map[tid]
            if not (t.release_time <= slot <= t.deadline):
                violations.append(f"F3 SLA Breach: Task {tid} assigned to slot {slot} outside [{t.release_time}, {t.deadline}].")
        else:
            violations.append(f"Unknown task {tid} in schedule.")

    # 3. Check F1 Conflict Exclusion
    for u, v in instance.conflicts:
        if u in schedule and v in schedule:
            if schedule[u] == schedule[v]:
                violations.append(f"F1 Conflict Breach: Task {u} and Task {v} both assigned to slot {schedule[u]}.")

    # 4. Check F2 4D Resource Capacity Limit per slot
    slot_usage = {s: [0, 0, 0, 0] for s in range(1, instance.K + 1)}
    for tid, slot in schedule.items():
        if 1 <= slot <= instance.K:
            r = task_map[tid].resources
            for m in range(4):
                slot_usage[slot][m] += r[m]

    for s in range(1, instance.K + 1):
        cap = instance.capacities[s - 1]  # 0-indexed capacities list
        for m in range(4):
            if slot_usage[s][m] > cap[m]:
                violations.append(f"F2 Capacity Breach: Slot {s}, Dim {m+1}: used {slot_usage[s][m]} > capacity {cap[m]}.")

    is_feasible = (len(violations) == 0)
    return {
        "feasible": is_feasible,
        "violations": violations
    }

def compute_penalty(instance: ProblemInstance, schedule: Dict[int, int], lambda_bal: float = 1.0) -> Tuple[float, float, float]:
    """
    Computes P_base, P_bal, and P_total = P_base + lambda_bal * P_bal.
    If schedule is incomplete or invalid, returns (inf, inf, inf).
    """
    validation = validate_schedule(instance, schedule)
    if not validation["feasible"]:
        return float('inf'), float('inf'), float('inf')

    task_map = {t.task_id: t for t in instance.tasks}
    
    # 1. Base Penalty: sum w_i * sigma(i)
    p_base = sum(task_map[tid].weight * slot for tid, slot in schedule.items())

    # 2. Load Imbalance Penalty: normalized variance per dimension
    slot_usage = {s: [0, 0, 0, 0] for s in range(1, instance.K + 1)}
    for tid, slot in schedule.items():
        r = task_map[tid].resources
        for m in range(4):
            slot_usage[slot][m] += r[m]

    p_bal = 0.0
    for m in range(4):
        u_m = []
        for s in range(1, instance.K + 1):
            c_sm = instance.capacities[s - 1][m]
            if c_sm > 0:
                u_sm = slot_usage[s][m] / c_sm
            else:
                u_sm = 0.0  # Guarded zero-capacity
            u_m.append(u_sm)
            
        avg_u = sum(u_m) / instance.K
        p_bal += sum((u_sm - avg_u) ** 2 for u_sm in u_m)

    p_total = p_base + lambda_bal * p_bal
    return p_base, p_bal, p_total
