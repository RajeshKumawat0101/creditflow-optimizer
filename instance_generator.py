import random
from typing import Tuple, List, Set
from models import Task, ProblemInstance

def generate_random_instance(
    num_tasks: int,
    edge_probability: float = 0.25,
    max_capacity: Tuple[int, int, int, int] = (100, 100, 100, 100),
    max_horizon: int = 150,
    seed: int = 42
) -> ProblemInstance:
    random.seed(seed)
    tasks: List[Task] = []
    
    for i in range(num_tasks):
        duration = random.randint(1, 10)
        release_time = random.randint(0, 20)
        slack = random.randint(duration, duration + 30)
        deadline = release_time + slack
        weight = round(random.uniform(1.0, 10.0), 2)
        
        # 4D resource demands scaled to capacities
        r1 = random.randint(5, max_capacity[0] // 3)
        r2 = random.randint(5, max_capacity[1] // 3)
        r3 = random.randint(5, max_capacity[2] // 3)
        r4 = random.randint(5, max_capacity[3] // 3)
        
        tasks.append(Task(
            task_id=i,
            duration=duration,
            release_time=release_time,
            deadline=deadline,
            weight=weight,
            resources=(r1, r2, r3, r4)
        ))

    # Generate Erdos-Renyi Random Conflict Graph
    conflicts: Set[Tuple[int, int]] = set()
    for u in range(num_tasks):
        for v in range(u + 1, num_tasks):
            if random.random() < edge_probability:
                conflicts.add((u, v))

    return ProblemInstance(
        tasks=tasks,
        conflicts=conflicts,
        resource_capacities=max_capacity,
        max_time_horizon=max_horizon
    )
