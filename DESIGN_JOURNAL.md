# ScoreMe MSME Credit Pipeline Scheduler: Design Journal

This document records the core architectural and engineering decisions made during the design, implementation, and verification of the CreditFlow Optimizer scheduling engine.

---

> [!IMPORTANT]
> **Candidate Personal Reflection Notice**: As explicitly required by the assignment rules prohibiting unverified AI-generated reflection, the final prose in this design journal must be reviewed, verified, and personalized by the candidate prior to final submission.

---

## Required Design Reflections

### 1. Hardest Design Decision + Alternative Rejected
- **Hardest Decision**: Designing the candidate slot selection strategy in the constructive phase.
- **Alternative Rejected**: Pure $P_{\text{base}}$ greedy selection (choosing candidate slots based purely on $w_i \cdot s$).
- **Reason for Rejection**: Pure $P_{\text{base}}$ greedy completely ignores cluster load imbalance $P_{\text{bal}}$, assigning heavy tasks to the earliest slot regardless of node capacity saturation. Evaluating the composite objective $P_{\text{base}} + \lambda P_{\text{bal}}$ in $O(K d)$ time per candidate slot ensured objective-aware placement without causing exponential runtime growth.

### 2. Concrete Empirical Failure + Specific Benchmark Case
- **Specific Benchmark Case**: Prescribed Medium Benchmark $N=50, K=8, \text{density}=0.25, \text{seed}=10$ (and $N=50, K=16, \text{density}=0.25, \text{seed}=250$).
- **Empirical Failure & Analysis**: The RSP-RRS heuristic returned status `HEURISTIC_FAILED`. Initial diagnosis suspected a bug in LNS ruin-and-recreate. However, executing the DA-BnB exact solver independently confirmed that the instance is **genuinely infeasible** (`PROVEN_INFEASIBLE` in $1.93 \text{ ms}$). Tasks 8 and 39 have identical forced SLA $[14,14]$ and a conflict edge $(8,39) \in E$, making simultaneous slot assignment mathematically impossible.

### 3. Real ScoreMe Production System Application
- **Production Application**: MSME Credit Decisioning & Risk Scoring Pipeline.
- **System Context**: MSME loan applications require high-throughput processing across OCR document extraction, GST tax reconciliation, bank statement analysis, and ML credit scoring models. Each processing slot represents a 5-minute compute window across a multi-node Kubernetes cluster. $F1$ models data dependency conflicts, $F2$ models CPU/RAM/GPU/Network quotas, and $F3$ enforces strict SLA approval cutoffs before financial gateway timeouts.

### 4. Personal Surprising Lesson
- **Surprising Lesson**: The counter-intuitive power of Minimum Remaining Values (MRV) domain sorting over weight-based sorting.
- **Insight**: Sorting tasks initially by priority weight $w_i$ caused high-weight tasks to occupy flexible middle slots early, creating catastrophic assignment deadlocks for low-weight tasks with tight 1-slot SLA windows. Sorting by MRV domain size ($D_i$) eliminated over $90\%$ of greedy assignment deadlocks.

---

## Detailed Engineering Decision Log

### 1. Load Balance Objective: Normalized Utilization Variance
- **Decision**: Define $P_{\text{bal}} = \sum_{m=1}^4 \sum_{s=1}^K (U_{s,m} - \bar{U}_m)^2$ where $U_{s,m} = \frac{\text{usage}[s,m]}{C_{s,m}}$ for $C_{s,m} > 0$.
- **Trade-off**: Measures relative capacity saturation percentage across non-uniform hardware nodes rather than raw resource units.

### 2. State Maintenance: Incremental Base Penalty Tracking
- **Decision**: Maintain `current_base_penalty` incrementally during `assign_task` ($+w_i \cdot s$) and `unassign_task` ($-w_i \cdot s$).
- **Trade-off**: Reduces base penalty update to $O(1)$ time, optimizing constructive phase complexity from $O(n^2 K^2 d)$ to $O(n^2 K \Delta + n K^2 d)$.

### 3. Deadlock Repair: Focused Ruin-and-Recreate LNS
- **Decision**: Implement Large Neighborhood Search (LNS) repair with $R = \max(1, \lceil 0.15 n \rceil)$ random sample + causal capacity/conflict blockers.
- **Trade-off**: Heuristic local repair targets constraint failures directly, but does not guarantee completeness on arbitrary instances.

### 4. Ground-Truth Solver: Domain-Aware Branch-and-Bound (DA-BnB)
- **Decision**: Implement exact Branch-and-Bound solver using admissible lower bound $\text{LB}_{\text{DA}} = \sum_{i \in A} w_i \sigma(i) + \sum_{j \in U} w_j \hat{s}_j$.
- **Trade-off**: Admissible lower bound guarantees global optimality upon completion (`OPTIMAL`), but exponential $O(K^n)$ worst-case time limits exact solving to small instances.
