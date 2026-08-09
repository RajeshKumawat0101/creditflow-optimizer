import sys
import json
import time
from typing import Dict, Any
from models import Task, ProblemInstance
from solvers.rsp_rrs import rsp_rrs_solve
from validator import validate_schedule, compute_penalty

def parse_json_input(input_data: Dict[str, Any]) -> Tuple[ProblemInstance, float]:
    """
    Parses a JSON input dictionary into a ProblemInstance and lambda_bal parameter.
    Expected JSON structure:
    {
      "n": 3,
      "K": 2,
      "lambda_bal": 1.0,
      "tasks": [
        {"task_id": 1, "duration": 1, "release_time": 1, "deadline": 2, "weight": 10.0, "resources": [5, 10, 0, 2]}, ...
      ],
      "conflicts": [[1, 2]],
      "capacities": [[100, 100, 100, 100], [100, 100, 100, 100]]
    }
    """
    n = input_data["n"]
    K = input_data["K"]
    lambda_bal = input_data.get("lambda_bal", 1.0)
    
    tasks = []
    for t_dict in input_data["tasks"]:
        tasks.append(Task(
            task_id=t_dict["task_id"],
            duration=t_dict.get("duration", 1),
            release_time=t_dict["release_time"],
            deadline=t_dict["deadline"],
            weight=float(t_dict["weight"]),
            resources=tuple(t_dict["resources"])
        ))
        
    conflicts = set(tuple(edge) for edge in input_data.get("conflicts", []))
    capacities = [tuple(cap) for cap in input_data["capacities"]]
    
    inst = ProblemInstance(n=n, K=K, tasks=tasks, conflicts=conflicts, capacities=capacities)
    return inst, lambda_bal

def main():
    """
    JSON CLI Interface Adapter.
    Usage:
        python run.py input.json
        cat input.json | python run.py
    """
    if len(sys.argv) > 1:
        with open(sys.argv[1], 'r') as f:
            raw_data = json.load(f)
    else:
        raw_data = json.load(sys.stdin)

    inst, lambda_bal = parse_json_input(raw_data)
    res = rsp_rrs_solve(inst, lambda_bal=lambda_bal)

    val = validate_schedule(inst, res.schedule)
    is_feasible = val["feasible"]
    
    if is_feasible:
        violation_reason = None
        penalty = res.penalty_total
    else:
        violation_reason = "; ".join(val["violations"]) if val["violations"] else "Heuristic failed to place all tasks within constraints."
        penalty = None

    # Output exact required JSON format
    output = {
        "assignment": {str(k): v for k, v in res.schedule.items()} if is_feasible else {},
        "penalty": penalty,
        "runtime_ms": round(res.runtime_ms, 2),
        "feasible": is_feasible,
        "violation_reason": violation_reason
    }

    print(json.dumps(output, indent=2))

if __name__ == '__main__':
    main()
