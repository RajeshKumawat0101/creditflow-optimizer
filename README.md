# ScoreMe MSME Credit Pipeline Scheduler

An enterprise-grade, mathematically verified credit decisioning pipeline task scheduler. Solves multi-dimensional resource-constrained scheduling under graph conflict exclusions and strict SLA window bounds.

---

## 1. Project Overview

The **ScoreMe MSME Credit Pipeline Scheduler** allocates $n$ credit decisioning tasks into $K$ processing time slots while jointly optimizing completion time penalties and multi-dimensional cluster load balance.

---

## 2. Mathematical Problem Formulation

Given $n$ tasks, $K$ processing slots, 4-dimensional resource capacity profiles $\mathbf{C}(s) = (C_{s,1}, C_{s,2}, C_{s,3}, C_{s,4})$, conflict graph $G = (V, E)$, priority weights $w_i > 0$, and SLA bounds $[l_i, u_i]$, find slot assignment $\sigma: \{1 \dots n\} \to \{1 \dots K\}$ minimizing:

$$\mathcal{P}(\sigma) = P_{\text{base}}(\sigma) + \lambda \cdot P_{\text{bal}}(\sigma)$$

where:
- **Weighted Start/Completion Penalty**: $P_{\text{base}}(\sigma) = \sum_{i=1}^n w_i \cdot \sigma(i)$
- **Cluster Load Imbalance Penalty**: $P_{\text{bal}}(\sigma) = \sum_{m=1}^4 \sum_{s=1}^K \left(U_{s,m} - \bar{U}_m\right)^2$
- **Normalized Utilization**: $U_{s,m} = \frac{\text{usage}[s,m]}{C_{s,m}}$ for $C_{s,m} > 0$, else $0.0$.
- **Mean Dimension Utilization**: $\bar{U}_m = \frac{1}{K} \sum_{s=1}^K U_{s,m}$.

---

## 3. Hard Constraint Definitions

- **F1: Conflict Exclusion**: Conflicting tasks cannot share the same processing slot.
  $$\forall (u, v) \in E \implies \sigma(u) \neq \sigma(v)$$
- **F2: 4D Capacity Limit**: Total resource consumption in any slot cannot exceed slot capacity across CPU, RAM, GPU, and Network.
  $$\forall s \in \{1 \dots K\}, m \in \{1 \dots 4\} \implies \sum_{i: \sigma(i) = s} r_{i,m} \le C_{s,m}$$
- **F3: Hard SLA Window**: Tasks must be assigned within their strict release and deadline window.
  $$\forall i \in \{1 \dots n\} \implies l_i \le \sigma(i) \le u_i$$

---

## 4. Solvers & Algorithms

### RSP-RRS Heuristic Solver (`solvers/rsp_rrs.py`)
Polynomial-time heuristic featuring:
1. **MRV Priority Construction**: Variable ordering using Minimum Remaining Values $D_i = |\{ s \in [l_i, u_i] \mid F1, F2 \text{ valid} \}|$.
2. **Objective-Aware Candidate Selection**: Evaluates composite penalty $P_{\text{base}} + \lambda P_{\text{bal}}$ in $O(K d)$ time per candidate slot.
3. **Focused Ruin-and-Recreate LNS**: Identifies capacity/conflict blockers for failed tasks and unassigns target blockers + $\max(1, \lceil 0.15 n \rceil)$ random sample to repair deadlocks.
4. **2-Opt Pairwise Swap Search**: Performs local search over pairwise task slot swaps to strictly reduce penalty.

### DA-BnB Exact Solver (`solvers/da_bnb.py`)
Domain-Aware Branch-and-Bound exact solver guaranteeing ground-truth optimal solutions or infeasibility proofs for small instances ($n \le 8$):
- **Admissible Lower Bound**: $\text{LB}_{\text{DA}}(\sigma_{\text{partial}}) = \sum_{i \in A} w_i \sigma(i) + \sum_{j \in U} w_j \hat{s}_j$.
- **Admissibility**: Ignores unassigned task interactions and $P_{\text{bal}} \ge 0$, maintaining $\text{LB}_{\text{DA}} \le \mathcal{P}(\sigma^*)$.

### Pure Brute-Force Baseline (`solvers/pure_brute_force.py`)
100% self-contained unpruned ground-truth solver enumerating all $K^n$ assignments without importing `validator.py` or solver helpers for independent cross-validation on $n \le 6$.

---

## 5. Solver Return Status Semantics

- **`OPTIMAL`**: Returned by exact solvers (`DA-BnB`, `Pure Brute Force`) when exhaustive search completes and proves global optimality.
- **`PROVEN_INFEASIBLE`**: Returned by exact solvers when exhaustive search proves zero feasible schedules exist.
- **`TIMEOUT`**: Returned by exact solvers if search exceeds time limit before proof.
- **`FEASIBLE`**: Returned by heuristic solver (`RSP-RRS`) when a valid schedule satisfying $F1, F2, F3$ is found.
- **`HEURISTIC_FAILED`**: Returned by heuristic solver when unassigned tasks remain after LNS iterations. **Does NOT claim infeasibility.**

---

## 6. Installation & Setup

```bash
# Requires Python 3.8+ with standard library
cd "d:/CreditFlow Optimizer"

# Compile all modules
python -m compileall .
```

---

## 7. Running Tests & Benchmarks

```bash
# Run full 20-scenario unit & adversarial test suite
python -m unittest test_suite.py

# Run executable benchmark runner
python benchmark_runner.py
```
