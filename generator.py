import random
from typing import Tuple, List, Set
from models import Task, ProblemInstance

def generate_instance(
    num_tasks: int,
    num_slots: int = 5,
    edge_probability: float = 0.2,
    max_capacity: Tuple[int, int, int, int] = (100, 100, 100, 100),
    max_demand_ratio: float = 0.4,
    seed: int = 42
) -> ProblemInstance:
    rng = random.Random(seed)
    tasks: List[Task] = []
    
    for i in range(1, num_tasks + 1):
        # SLA release and deadline within 1...K
        l_i = rng.randint(1, max(1, num_slots - 1))
        u_i = rng.randint(l_i, num_slots)
        w_i = round(rng.uniform(1.0, 10.0), 2)
        
        # 4D resource demands scaled to capacities
        r1 = rng.randint(1, max(1, int(max_capacity[0] * max_demand_ratio)))
        r2 = rng.randint(1, max(1, int(max_capacity[1] * max_demand_ratio)))
        r3 = rng.randint(1, max(1, int(max_capacity[2] * max_demand_ratio)))
        r4 = rng.randint(1, max(1, int(max_capacity[3] * max_demand_ratio)))
        
        tasks.append(Task(
            task_id=i,
            duration=1,
            release_time=l_i,
            deadline=u_i,
            weight=w_i,
            resources=(r1, r2, r3, r4)
        ))

    # Erdos-Renyi Conflict Graph
    conflicts: Set[Tuple[int, int]] = set()
    for u in range(1, num_tasks + 1):
        for v in range(u + 1, num_tasks + 1):
            if rng.random() < edge_probability:
                conflicts.add((u, v))

    capacities = [max_capacity for _ in range(num_slots)]

    return ProblemInstance(
        n=num_tasks,
        K=num_slots,
        tasks=tasks,
        conflicts=conflicts,
        capacities=capacities
    )
