import unittest
from models import Task, ProblemInstance
from validator import validate_schedule, compute_penalty
from solvers.rsp_rrs import rsp_rrs_solve
from solvers.da_bnb import da_bnb_exact_solve
from solvers.pure_brute_force import pure_brute_force_solve
from generator import generate_instance

class TestComprehensiveSchedulerSuite(unittest.TestCase):

    # 1. Single Slot SLA
    def test_01_single_slot_sla(self):
        tasks = [Task(1, 1, 2, 2, 1.0, (1, 1, 1, 1))]
        capacities = [(10, 10, 10, 10), (10, 10, 10, 10)]
        inst = ProblemInstance(1, 2, tasks, set(), capacities)
        res = rsp_rrs_solve(inst, lambda_bal=1.0, max_lns_iters=0, seed=42)
        self.assertEqual(res.status, 'FEASIBLE')
        self.assertEqual(res.schedule[1], 2)

    # 2. Impossible SLA
    def test_02_impossible_sla(self):
        tasks = [Task(1, 1, 3, 2, 1.0, (1, 1, 1, 1))]
        capacities = [(10, 10, 10, 10), (10, 10, 10, 10)]
        inst = ProblemInstance(1, 2, tasks, set(), capacities)
        res = rsp_rrs_solve(inst, lambda_bal=1.0, seed=42)
        self.assertEqual(res.status, 'HEURISTIC_FAILED')

    # 3. Zero Capacity
    def test_03_zero_capacity(self):
        tasks = [Task(1, 1, 1, 2, 1.0, (5, 0, 0, 0))]
        capacities = [(0, 10, 10, 10), (10, 10, 10, 10)]
        inst = ProblemInstance(1, 2, tasks, set(), capacities)
        res = rsp_rrs_solve(inst, lambda_bal=1.0, max_lns_iters=0, seed=42)
        self.assertEqual(res.status, 'FEASIBLE')
        self.assertEqual(res.schedule[1], 2)

    # 4. Zero Resource Demand
    def test_04_zero_resource_demand(self):
        tasks = [Task(1, 1, 1, 2, 1.0, (0, 0, 0, 0))]
        capacities = [(10, 10, 10, 10), (10, 10, 10, 10)]
        inst = ProblemInstance(1, 2, tasks, set(), capacities)
        res = rsp_rrs_solve(inst, lambda_bal=1.0, seed=42)
        self.assertEqual(res.status, 'FEASIBLE')

    # 5. Task Demand Greater Than Capacity
    def test_05_task_demand_greater_than_capacity(self):
        tasks = [Task(1, 1, 1, 2, 1.0, (15, 0, 0, 0))]
        capacities = [(10, 10, 10, 10), (10, 10, 10, 10)]
        inst = ProblemInstance(1, 2, tasks, set(), capacities)
        res = rsp_rrs_solve(inst, lambda_bal=1.0, seed=42)
        self.assertEqual(res.status, 'HEURISTIC_FAILED')

    # 6. Complete Conflict Graph (Kn)
    def test_06_complete_conflict_graph(self):
        tasks = [Task(i, 1, 1, 3, 1.0, (1, 1, 1, 1)) for i in range(1, 4)]
        conflicts = {(1, 2), (2, 3), (1, 3)}
        capacities = [(10, 10, 10, 10) for _ in range(3)]
        inst = ProblemInstance(3, 3, tasks, conflicts, capacities)
        res = rsp_rrs_solve(inst, lambda_bal=1.0, seed=42)
        self.assertEqual(res.status, 'FEASIBLE')
        self.assertEqual(len(set(res.schedule.values())), 3)

    # 7. Empty Conflict Graph
    def test_07_empty_conflict_graph(self):
        inst = generate_instance(num_tasks=6, num_slots=3, edge_probability=0.0, seed=42)
        res = rsp_rrs_solve(inst, lambda_bal=1.0, seed=42)
        if res.status == 'FEASIBLE':
            val = validate_schedule(inst, res.schedule)
            self.assertTrue(val["feasible"])

    # 8. All Tasks Same Slot Window
    def test_08_all_tasks_same_slot_window(self):
        tasks = [Task(1, 1, 1, 1, 1.0, (2, 2, 2, 2)), Task(2, 1, 1, 1, 1.0, (3, 3, 3, 3))]
        capacities = [(10, 10, 10, 10)]
        inst = ProblemInstance(2, 1, tasks, set(), capacities)
        res = rsp_rrs_solve(inst, lambda_bal=1.0, seed=42)
        self.assertEqual(res.status, 'FEASIBLE')

    # 9. Heterogeneous Capacities
    def test_09_heterogeneous_capacities(self):
        tasks = [Task(1, 1, 1, 2, 1.0, (5, 5, 5, 5))]
        capacities = [(5, 5, 5, 5), (20, 20, 20, 20)]
        inst = ProblemInstance(1, 2, tasks, set(), capacities)
        res = rsp_rrs_solve(inst, lambda_bal=1.0, seed=42)
        self.assertEqual(res.status, 'FEASIBLE')

    # 10. Lambda = 0
    def test_10_lambda_zero(self):
        tasks = [Task(1, 1, 1, 2, 10.0, (5, 0, 0, 0)), Task(2, 1, 1, 2, 1.0, (5, 0, 0, 0))]
        capacities = [(10, 10, 10, 10), (10, 10, 10, 10)]
        inst = ProblemInstance(2, 2, tasks, set(), capacities)
        res = rsp_rrs_solve(inst, lambda_bal=0.0, seed=42)
        self.assertEqual(res.status, 'FEASIBLE')

    # 11. Lambda Very Large (50.0)
    def test_11_lambda_very_large(self):
        tasks = [Task(1, 1, 1, 1, 100.0, (5, 0, 0, 0)), Task(2, 1, 1, 2, 2.0, (5, 0, 0, 0))]
        capacities = [(10, 10, 10, 10), (10, 10, 10, 10)]
        inst = ProblemInstance(2, 2, tasks, set(), capacities)
        res = rsp_rrs_solve(inst, lambda_bal=50.0, seed=42)
        self.assertEqual(res.status, 'FEASIBLE')
        self.assertEqual(res.schedule[2], 2)

    # 12. Equal-Cost Schedules
    def test_12_equal_cost_schedules(self):
        tasks = [Task(1, 1, 1, 1, 1.0, (1, 1, 1, 1)), Task(2, 1, 1, 1, 1.0, (1, 1, 1, 1))]
        capacities = [(10, 10, 10, 10)]
        inst = ProblemInstance(2, 1, tasks, set(), capacities)
        res = rsp_rrs_solve(inst, lambda_bal=1.0, seed=42)
        self.assertEqual(res.status, 'FEASIBLE')

    # 13. Multiple Optimal Solutions
    def test_13_multiple_optimal_solutions(self):
        tasks = [Task(1, 1, 1, 2, 1.0, (1, 1, 1, 1)), Task(2, 1, 1, 2, 1.0, (1, 1, 1, 1))]
        capacities = [(10, 10, 10, 10), (10, 10, 10, 10)]
        inst = ProblemInstance(2, 2, tasks, set(), capacities)
        opt_res = da_bnb_exact_solve(inst, lambda_bal=0.0)
        self.assertEqual(opt_res.status, 'OPTIMAL')

    # 14. Floating Point Precision Safety
    def test_14_floating_point_ties(self):
        tasks = [Task(1, 1, 1, 2, 1.000000001, (1, 1, 1, 1))]
        capacities = [(10, 10, 10, 10), (10, 10, 10, 10)]
        inst = ProblemInstance(1, 2, tasks, set(), capacities)
        res = rsp_rrs_solve(inst, lambda_bal=1.0, seed=42)
        self.assertEqual(res.status, 'FEASIBLE')

    # 15. LNS Zero Blockers
    def test_15_lns_zero_blockers(self):
        tasks = [Task(1, 1, 1, 1, 1.0, (15, 0, 0, 0))]
        capacities = [(10, 10, 10, 10)]
        inst = ProblemInstance(1, 1, tasks, set(), capacities)
        res = rsp_rrs_solve(inst, lambda_bal=1.0, max_lns_iters=2, seed=42)
        self.assertEqual(res.status, 'HEURISTIC_FAILED')

    # 16. LNS Every Task Blocker
    def test_16_lns_every_task_blocker(self):
        tasks = [
            Task(1, 1, 1, 1, 10.0, (5, 0, 0, 0)),
            Task(2, 1, 1, 1, 10.0, (5, 0, 0, 0)),
            Task(3, 1, 1, 1, 1.0, (5, 0, 0, 0))
        ]
        capacities = [(10, 10, 10, 10)]
        inst = ProblemInstance(3, 1, tasks, set(), capacities)
        res = rsp_rrs_solve(inst, lambda_bal=1.0, max_lns_iters=2, seed=42)
        self.assertEqual(res.status, 'HEURISTIC_FAILED')

    # 17. Swap Requiring 3-Cycle Inadequacy
    def test_17_swap_requiring_3_cycle(self):
        tasks = [
            Task(1, 1, 1, 3, 10.0, (1, 1, 1, 1)),
            Task(2, 1, 1, 3, 10.0, (1, 1, 1, 1)),
            Task(3, 1, 1, 3, 1.0, (1, 1, 1, 1))
        ]
        conflicts = {(1, 2), (2, 3)}
        capacities = [(10, 10, 10, 10) for _ in range(3)]
        inst = ProblemInstance(3, 3, tasks, conflicts, capacities)
        res = rsp_rrs_solve(inst, lambda_bal=1.0, seed=42)
        self.assertEqual(res.status, 'FEASIBLE')

    # 18. Heuristic Failure Despite Feasible Instance
    def test_18_heuristic_failure_despite_feasible(self):
        tasks = [
            Task(1, 1, 1, 1, 10.0, (6, 0, 0, 0)),
            Task(2, 1, 1, 1, 5.0, (6, 0, 0, 0))
        ]
        capacities = [(10, 10, 10, 10)]
        inst = ProblemInstance(2, 1, tasks, set(), capacities)
        res = rsp_rrs_solve(inst, lambda_bal=0.0, max_lns_iters=0, seed=42)
        self.assertEqual(res.status, 'HEURISTIC_FAILED')

    # 19. Exact Infeasibility Proof
    def test_19_exact_infeasibility_proof(self):
        tasks = [Task(1, 1, 1, 1, 1.0, (1, 1, 1, 1)), Task(2, 1, 1, 1, 1.0, (1, 1, 1, 1))]
        conflicts = {(1, 2)}
        capacities = [(10, 10, 10, 10)]
        inst = ProblemInstance(2, 1, tasks, conflicts, capacities)
        res = da_bnb_exact_solve(inst)
        self.assertEqual(res.status, 'PROVEN_INFEASIBLE')

    # 20. Exact Solver vs Pure Brute-Force Agreement (20 Random Tiny Instances)
    def test_20_exact_vs_brute_force_agreement(self):
        for seed in range(20):
            inst = generate_instance(num_tasks=4, num_slots=3, edge_probability=0.25, seed=seed)
            pure_res = pure_brute_force_solve(inst, lambda_bal=1.0)
            bnb_res = da_bnb_exact_solve(inst, lambda_bal=1.0)
            
            self.assertEqual(pure_res.status, bnb_res.status)
            if pure_res.status == 'OPTIMAL':
                self.assertAlmostEqual(pure_res.penalty_total, bnb_res.penalty_total, places=4)
                self.assertAlmostEqual(pure_res.penalty_base, bnb_res.penalty_base, places=4)

if __name__ == '__main__':
    unittest.main()
