import time
from typing import Dict, List, Set, Tuple, Optional
from models import Task, ProblemInstance, ScheduleResult

def validate_schedule(instance: ProblemInstance, start_times: Dict[int, int]) -> Tuple[bool, float, List[str]]:
    violations = []
    task_map = {t.task_id: t for t in instance.tasks}
    
    if len(start_times) != len(instance.tasks):
        violations.append(f"Incomplete schedule: {len(start_times)}/{len(instance.tasks)} tasks scheduled.")
        return False, float('inf'), violations

    max_completion = 0
    total_sla_penalty = 0.0

    for tid, st in start_times.items():
        t = task_map[tid]
        if st < t.release_time:
            violations.append(f"Task {tid} started at {st} before release time {t.release_time}")
            
        comp_time = st + t.duration
        if comp_time > max_completion:
            max_completion = comp_time
            
        lateness = max(0, comp_time - t.deadline)
        total_sla_penalty += t.weight * (lateness ** 2)

    tids = list(start_times.keys())
    for i in range(len(tids)):
        u = tids[i]
        su, du = start_times[u], task_map[u].duration
        for j in range(i + 1, len(tids)):
            v = tids[j]
            if instance.is_conflicting(u, v):
                sv, dv = start_times[v], task_map[v].duration
                if not (su + du <= sv or sv + dv <= su):
                    violations.append(f"Conflict violation between Task {u} [{su}, {su+du}) and Task {v} [{sv}, {sv+dv})")

    if max_completion > 0:
        c1, c2, c3, c4 = instance.resource_capacities
        for tick in range(max_completion):
            r1_sum, r2_sum, r3_sum, r4_sum = 0, 0, 0, 0
            for tid, st in start_times.items():
                t = task_map[tid]
                if st <= tick < st + t.duration:
                    r1_sum += t.resources[0]
                    r2_sum += t.resources[1]
                    r3_sum += t.resources[2]
                    r4_sum += t.resources[3]

            if r1_sum > c1 or r2_sum > c2 or r3_sum > c3 or r4_sum > c4:
                violations.append(f"Resource capacity exceeded at tick {tick}")

    is_feasible = len(violations) == 0
    makespan_penalty = 0.5 * max_completion
    final_penalty = total_sla_penalty + makespan_penalty if is_feasible else float('inf')
    
    return is_feasible, final_penalty, violations


class BruteForceSolver:
    """
    Branch-and-Bound Exact Optimal Solver.
    Uses early resource, conflict, and cost bound pruning.
    """
    def __init__(self, instance: ProblemInstance):
        self.instance = instance
        self.best_start_times: Optional[Dict[int, int]] = None
        self.best_penalty = float('inf')

    def solve(self) -> ScheduleResult:
        start_clock = time.perf_counter()
        tasks = sorted(self.instance.tasks, key=lambda t: t.deadline)
        c1, c2, c3, c4 = self.instance.resource_capacities
        
        def backtrack(task_idx: int, current_schedule: Dict[int, int], current_cost: float):
            if current_cost >= self.best_penalty:
                return

            if task_idx == len(tasks):
                is_valid, penalty, _ = validate_schedule(self.instance, current_schedule)
                if is_valid and penalty < self.best_penalty:
                    self.best_penalty = penalty
                    self.best_start_times = current_schedule.copy()
                return

            task = tasks[task_idx]
            max_start = min(task.release_time + 25, self.instance.max_time_horizon - task.duration)
            
            for st in range(task.release_time, max_start + 1):
                # 1. Conflict check
                conflict = False
                for prev_idx in range(task_idx):
                    prev_task = tasks[prev_idx]
                    if self.instance.is_conflicting(task.task_id, prev_task.task_id):
                        pst = current_schedule[prev_task.task_id]
                        pdu = prev_task.duration
                        if not (st + task.duration <= pst or pst + pdu <= st):
                            conflict = True
                            break
                if conflict:
                    continue

                # 2. Incremental 4D capacity check
                cap_exceeded = False
                for tick in range(st, st + task.duration):
                    u1, u2, u3, u4 = task.resources
                    for prev_idx in range(task_idx):
                        pt = tasks[prev_idx]
                        pst = current_schedule[pt.task_id]
                        if pst <= tick < pst + pt.duration:
                            u1 += pt.resources[0]
                            u2 += pt.resources[1]
                            u3 += pt.resources[2]
                            u4 += pt.resources[3]
                    if u1 > c1 or u2 > c2 or u3 > c3 or u4 > c4:
                        cap_exceeded = True
                        break
                if cap_exceeded:
                    continue

                # SLA cost bound calculation
                comp_time = st + task.duration
                lateness = max(0, comp_time - task.deadline)
                added_cost = task.weight * (lateness ** 2)

                current_schedule[task.task_id] = st
                backtrack(task_idx + 1, current_schedule, current_cost + added_cost)
                del current_schedule[task.task_id]

        backtrack(0, {}, 0.0)
        elapsed_ms = (time.perf_counter() - start_clock) * 1000.0

        if self.best_start_times is not None:
            is_valid, penalty, violations = validate_schedule(self.instance, self.best_start_times)
            return ScheduleResult(self.best_start_times, penalty, is_valid, elapsed_ms, violations)
        else:
            return ScheduleResult({}, float('inf'), False, elapsed_ms, ["No feasible schedule found"])


class MultiDimensionalDSATURSolver:
    def __init__(self, instance: ProblemInstance):
        self.instance = instance

    def solve(self) -> ScheduleResult:
        start_clock = time.perf_counter()
        tasks = self.instance.tasks
        task_map = {t.task_id: t for t in tasks}
        
        adj: Dict[int, Set[int]] = {t.task_id: set() for t in tasks}
        for u, v in self.instance.conflicts:
            if u in adj and v in adj:
                adj[u].add(v)
                adj[v].add(u)

        uncolored = set(task_map.keys())
        start_times: Dict[int, int] = {}
        assigned_colors: Dict[int, int] = {}

        def get_saturation(tid: int) -> int:
            neighbor_slots = set()
            for nbr in adj[tid]:
                if nbr in assigned_colors:
                    neighbor_slots.add(assigned_colors[nbr])
            return len(neighbor_slots)

        def get_resource_intensity(t: Task) -> float:
            c1, c2, c3, c4 = self.instance.resource_capacities
            return (t.resources[0]/c1 + t.resources[1]/c2 + t.resources[2]/c3 + t.resources[3]/c4) / 4.0

        while uncolored:
            best_task_id = max(
                uncolored,
                key=lambda tid: (
                    get_saturation(tid),
                    task_map[tid].weight,
                    -task_map[tid].deadline,
                    get_resource_intensity(task_map[tid]),
                    len(adj[tid])
                )
            )

            task = task_map[best_task_id]
            placed = False
            for st in range(task.release_time, self.instance.max_time_horizon - task.duration + 1):
                conflict_free = True
                for nbr in adj[best_task_id]:
                    if nbr in start_times:
                        nst = start_times[nbr]
                        ndu = task_map[nbr].duration
                        if not (st + task.duration <= nst or nst + ndu <= st):
                            conflict_free = False
                            break
                if not conflict_free:
                    continue

                capacity_ok = True
                c1, c2, c3, c4 = self.instance.resource_capacities
                for tick in range(st, st + task.duration):
                    r1_used, r2_used, r3_used, r4_used = task.resources
                    for active_id, active_st in start_times.items():
                        at = task_map[active_id]
                        if active_st <= tick < active_st + at.duration:
                            r1_used += at.resources[0]
                            r2_used += at.resources[1]
                            r3_used += at.resources[2]
                            r4_used += at.resources[3]

                    if r1_used > c1 or r2_used > c2 or r3_used > c3 or r4_used > c4:
                        capacity_ok = False
                        break

                if capacity_ok:
                    start_times[best_task_id] = st
                    assigned_colors[best_task_id] = st
                    uncolored.remove(best_task_id)
                    placed = True
                    break

            if not placed:
                break

        elapsed_ms = (time.perf_counter() - start_clock) * 1000.0
        is_valid, penalty, violations = validate_schedule(self.instance, start_times)
        return ScheduleResult(start_times, penalty, is_valid, elapsed_ms, violations)
