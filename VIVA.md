# ScoreMe MSME Credit Pipeline Scheduler: Viva & Interview Defense Guide

This guide contains the 20 most important viva questions, concise defensive answers, code mappings, and a fresh 6-node manual algorithm trace.

---

## 1. Algorithm Walkthrough & Code Mapping

The scheduling engine consists of 3 primary modules:
1. **Validator & Objective Authority** (`validator.py`): `validate_schedule` independently checks $F1, F2, F3$, and `compute_penalty` evaluates $P_{\text{base}} + \lambda P_{\text{bal}}$.
2. **RSP-RRS Heuristic Solver** (`solvers/rsp_rrs.py`):
   - `compute_domain_size`: Calculates valid slot domain size $D_i = |\{s \in [l_i, u_i] \mid F1, F2 \text{ valid}\}|$.
   - `evaluate_candidate_slot_objective`: Evaluates $P_{\text{base}} + \lambda P_{\text{bal}}$ in $O(K d)$ time per candidate slot.
   - `identify_causal_blockers`: Isolates $F1$ edge conflicts and $F2$ capacity deficit contributors.
   - Phase 1 Constructive Loop $\to$ Phase 2 LNS Repair Loop $\to$ Phase 3 2-Opt Pairwise Swap Search.
3. **Exact Solvers** (`solvers/da_bnb.py`, `solvers/pure_brute_force.py`): Domain-Aware Branch-and-Bound solver using admissible lower bound $\text{LB}_{\text{DA}}$, and an unpruned pure brute-force baseline.

---

## 2. Fresh 6-Node Manual Algorithm Trace

### Instance Setup
- **Tasks**: $n=6$, $K=3$ slots, $\mathbf{C}(s) = (10, 10, 10, 10)$ for $s \in \{1, 2, 3\}$.
- **Tasks**:
  - $t_1$: SLA $[1, 1]$, $w_1 = 10$, $\mathbf{r}_1 = (4, 4, 0, 0)$
  - $t_2$: SLA $[1, 2]$, $w_2 = 8$,  $\mathbf{r}_2 = (5, 5, 0, 0)$
  - $t_3$: SLA $[2, 3]$, $w_3 = 5$,  $\mathbf{r}_3 = (6, 6, 0, 0)$
  - $t_4$: SLA $[2, 2]$, $w_4 = 4$,  $\mathbf{r}_4 = (3, 3, 0, 0)$
  - $t_5$: SLA $[1, 3]$, $w_5 = 2$,  $\mathbf{r}_5 = (2, 2, 0, 0)$
  - $t_6$: SLA $[3, 3]$, $w_6 = 1$,  $\mathbf{r}_6 = (4, 4, 0, 0)$
- **Conflict Edge**: $(t_1, t_2) \in E$ (Tasks 1 and 2 cannot share a slot).

### Step-by-Step Execution Trace

| Step | Unassigned Tasks | MRV Pick | Reason | Selected Slot | Slot Usage after Step | Objective $\mathcal{P}$ |
|---|---|---|---|---|---|---|
| **0** | $\{1,2,3,4,5,6\}$ | - | Initial state | - | $S_1=0, S_2=0, S_3=0$ | $0.0$ |
| **1** | $\{1,2,3,4,5,6\}$ | **Task 1** | $D_1=1$ ($[1,1]$) | **Slot 1** | $S_1=(4,4), S_2=0, S_3=0$ | $10.0$ |
| **2** | $\{2,3,4,5,6\}$ | **Task 4** | $D_4=1$ ($[2,2]$) | **Slot 2** | $S_1=(4,4), S_2=(3,3), S_3=0$ | $18.0$ |
| **3** | $\{2,3,5,6\}$ | **Task 6** | $D_6=1$ ($[3,3]$) | **Slot 3** | $S_1=(4,4), S_2=(3,3), S_3=(4,4)$ | $21.0$ |
| **4** | $\{2,3,5\}$ | **Task 2** | $D_2=1$ (Slot 1 blocked by $t_1$ edge, SLA $[1,2] \implies$ Slot 2) | **Slot 2** | $S_1=(4,4), S_2=(8,8), S_3=(4,4)$ | $37.0$ |
| **5** | $\{3,5\}$ | **Task 3** | $D_3=1$ (Slot 2 full $8+6>10 \implies$ Slot 3) | **Slot 3** | $S_1=(4,4), S_2=(8,8), S_3=(10,10)$ | $52.0$ |
| **6** | $\{5\}$ | **Task 5** | $D_5=1$ (Slots 2 & 3 full $\implies$ Slot 1) | **Slot 1** | $S_1=(6,6), S_2=(8,8), S_3=(10,10)$ | $54.0$ |

**Final Schedule**: $\{1: 1, 2: 2, 3: 3, 4: 2, 5: 1, 6: 3\}$. All constraints $F1, F2, F3$ satisfied!

---

## 3. Advanced Technical Viva Questions

#### Q1: How would you extend the solver to support a 5th resource dimension (e.g., Disk IOPS)?
- **Answer**: Update `Task.resources` and `ProblemInstance.capacities` tuple size to 5. The normalized utilization loop in `validator.py` and `solvers/rsp_rrs.py` iterates `range(5)` instead of `range(4)`. Time complexity remains $O(n^2 K \Delta + n K^2 d)$ where $d=5$.

#### Q2: How does normalized utilization handle heterogeneous slot capacities?
- **Answer**: $U_{s,m} = \frac{\text{usage}[s,m]}{C_{s,m}} \in [0, 1]$ measures percentage capacity saturation rather than raw resource units. A slot with $C_{s,1} = 200$ carrying $100$ units has $U_{s,1} = 0.5$, matching a slot with $C_{s,1} = 50$ carrying $25$ units.

#### Q3: What design change would you make in hindsight?
- **Answer**: I would replace string-based status returns with explicit Enum classes (`Status.OPTIMAL`, `Status.PROVEN_INFEASIBLE`), and implement graph conflict checking using SIMD bitmasks for $O(1)$ adjacency checks during local search.

#### Q4: Why is DA-BnB lower bound admissible despite omitting $P_{\text{bal}}$?
- **Answer**: $P_{\text{bal}} \ge 0$ is a non-negative sum of squares. For $\lambda \ge 0$, $\mathcal{P} = P_{\text{base}} + \lambda P_{\text{bal}} \ge P_{\text{base}} \ge \text{LB}_{\text{DA}}$. Omitting $P_{\text{bal}}$ maintains strict admissibility ($\text{LB}_{\text{DA}} \le \mathcal{P}^*$).
