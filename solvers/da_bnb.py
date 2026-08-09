import time
from typing import Dict, List, Set, Tuple, Optional
from models import ProblemInstance, ScheduleResult
from validator import validate_schedule, compute_penalty

class DomainAwareBranchAndBoundSolver:
    """
    Domain-Aware Admissible Branch-and-Bound Exact Solver (DA-BnB).
    Computes ground-truth P_OPT for small instances (n <= 8).
    Evaluates complete objective P_total = P_base + lambda_bal * P_bal at leaf nodes.
    Uses admissible lower bound LB_DA = P_base(assigned) + sum_{unassigned} w_j * s_hat_j.
    """
    def __init__(self, instance: ProblemInstance, lambda_bal: float = 1.0):
        self.inst = instance
        self.lambda_bal = lambda_bal
        self.n = instance.n
        self.K = instance.K
        self.task_map = {t.task_id: t for t in instance.tasks}
        
        self.adj: Dict[int, Set[int]] = {i: set() for i in range(1, self.n + 1)}
        for u, v in instance.conflicts:
            if u in self.adj and v in self.adj:
                self.adj[u].add(v)
                self.adj[v].add(u)

        self.best_schedule: Optional[Dict[int, int]] = None
        self.best_cost = float('inf')
        self.searched_nodes = 0

    def solve(self) -> ScheduleResult:
        start_clock = time.perf_counter()
        
        schedule: Dict[int, int] = {}
        usage = [[0, 0, 0, 0] for _ in range(self.K + 1)]

        def is_f1_valid(tid: int, slot: int) -> bool:
            return not any(schedule.get(nbr) == slot for nbr in self.adj[tid])

        def is_f2_valid(tid: int, slot: int) -> bool:
            r = self.task_map[tid].resources
            cap = self.inst.capacities[slot - 1]
            return all(usage[slot][m] + r[m] <= cap[m] for m in range(4))

        def assign_task(tid: int, slot: int):
            schedule[tid] = slot
            r = self.task_map[tid].resources
            for m in range(4):
                usage[slot][m] += r[m]

        def unassign_task(tid: int):
            slot = schedule[tid]
            r = self.task_map[tid].resources
            for m in range(4):
                usage[slot][m] -= r[m]
            del schedule[tid]

        def compute_min_valid_slot(tid: int) -> int:
            t = self.task_map[tid]
            for s in range(t.release_time, t.deadline + 1):
                if is_f1_valid(tid, s) and is_f2_valid(tid, s):
                    return s
            return -1

        def backtrack(unassigned: Set[int]):
            self.searched_nodes += 1

            if not unassigned:
                p_base, p_bal, p_total = compute_penalty(self.inst, schedule, self.lambda_bal)
                if p_total < self.best_cost - 1e-9:
                    self.best_cost = p_total
                    self.best_schedule = schedule.copy()
                return

            current_assigned_base = sum(self.task_map[tid].weight * slot for tid, slot in schedule.items())
            lb_unassigned = 0.0
            
            best_next_tid = -1
            best_domain_size = float('inf')

            for tid in unassigned:
                s_hat = compute_min_valid_slot(tid)
                if s_hat == -1:
                    return
                
                t = self.task_map[tid]
                lb_unassigned += t.weight * s_hat

                dom_size = sum(1 for s in range(t.release_time, t.deadline + 1) if is_f1_valid(tid, s) and is_f2_valid(tid, s))
                if dom_size < best_domain_size:
                    best_domain_size = dom_size
                    best_next_tid = tid

            # Precision-safe admissible lower bound pruning check
            lb_total = current_assigned_base + lb_unassigned
            if lb_total >= self.best_cost - 1e-9:
                return

            t_branch = self.task_map[best_next_tid]
            unassigned.remove(best_next_tid)

            for s in range(t_branch.release_time, t_branch.deadline + 1):
                if is_f1_valid(best_next_tid, s) and is_f2_valid(best_next_tid, s):
                    assign_task(best_next_tid, s)
                    backtrack(unassigned)
                    unassign_task(best_next_tid)

            unassigned.add(best_next_tid)

        all_tasks = set(range(1, self.n + 1))
        backtrack(all_tasks)

        elapsed_ms = (time.perf_counter() - start_clock) * 1000.0

        if self.best_schedule is None:
            return ScheduleResult(
                status='PROVEN_INFEASIBLE',
                schedule={},
                penalty_base=float('inf'),
                penalty_bal=float('inf'),
                penalty_total=float('inf'),
                runtime_ms=elapsed_ms,
                violations=["Exhaustive search proved instance is infeasible"]
            )

        p_base, p_bal, p_total = compute_penalty(self.inst, self.best_schedule, self.lambda_bal)
        val = validate_schedule(self.inst, self.best_schedule)

        return ScheduleResult(
            status='OPTIMAL',
            schedule=self.best_schedule,
            penalty_base=p_base,
            penalty_bal=p_bal,
            penalty_total=p_total,
            runtime_ms=elapsed_ms,
            violations=val["violations"]
        )

def da_bnb_exact_solve(instance: ProblemInstance, lambda_bal: float = 1.0) -> ScheduleResult:
    solver = DomainAwareBranchAndBoundSolver(instance, lambda_bal)
    return solver.solve()
