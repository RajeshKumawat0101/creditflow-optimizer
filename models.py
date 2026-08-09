from dataclasses import dataclass, field
from typing import List, Tuple, Set, Dict, Optional

@dataclass
class Task:
    task_id: int
    duration: int                                # Execution duration (default 1 for unit task)
    release_time: int                            # l_i (1-indexed start slot)
    deadline: int                                # u_i (1-indexed end slot)
    weight: float                                # Priority weight w_i
    resources: Tuple[int, int, int, int]         # 4D demand vector r_i = (r1, r2, r3, r4)

@dataclass
class ProblemInstance:
    n: int
    K: int
    tasks: List[Task]                            # 1-indexed tasks: tasks[1...n]
    conflicts: Set[Tuple[int, int]]              # Undirected edges (u, v)
    capacities: List[Tuple[int, int, int, int]]  # 1-indexed capacities: capacities[1...K]

    def is_conflicting(self, u: int, v: int) -> bool:
        return (u, v) in self.conflicts or (v, u) in self.conflicts

@dataclass
class ScheduleResult:
    status: str                                  # 'FEASIBLE', 'HEURISTIC_FAILED', 'PROVEN_INFEASIBLE'
    schedule: Dict[int, int]                     # task_id -> slot (1-indexed)
    penalty_base: float
    penalty_bal: float
    penalty_total: float
    runtime_ms: float
    violations: List[str] = field(default_factory=list)
