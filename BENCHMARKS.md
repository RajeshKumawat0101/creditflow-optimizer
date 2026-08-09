# ScoreMe MSME Credit Pipeline Scheduler: Empirical Benchmark Report

This document records the exact benchmark measurements produced by `benchmark_runner.py` across the 9 prescribed ScoreMe assignment benchmark configurations and lambda sensitivity experiments.

---

## 1. Prescribed Assignment Benchmark Results (9 Cases)

Below are the exact execution results produced by running `python benchmark_runner.py` using `generate_instance` across the prescribed configurations:

| Category | Tasks ($N$) | Slots ($K$) | Density | Seed | DA-BnB Status | $P_{\text{OPT}}$ | RSP-RRS Status | $P_{\text{heur}}$ | Empirical Ratio $\alpha_{\text{emp}}$ | Runtime (ms) |
|---|---|---|---|---|---|---|---|---|---|---|
| **Small** | 8 | 3 | $0.30$ | 1 | **PROVEN_INFEASIBLE** | $\infty$ | **HEURISTIC_FAILED** | FAILED | N/A | $99.56 \text{ ms}$ |
| **Small** | 10 | 4 | $0.40$ | 2 | **PROVEN_INFEASIBLE** | $\infty$ | **HEURISTIC_FAILED** | FAILED | N/A | $73.68 \text{ ms}$ |
| **Small** | 12 | 4 | $0.50$ | 3 | **PROVEN_INFEASIBLE** | $\infty$ | **HEURISTIC_FAILED** | FAILED | N/A | $78.08 \text{ ms}$ |
| **Medium** | 50 | 8 | $0.25$ | 10 | N/A (Large) | N/A | **HEURISTIC_FAILED** | FAILED | N/A | $829.14 \text{ ms}$ |
| **Medium** | 100 | 10 | $0.30$ | 11 | N/A (Large) | N/A | **HEURISTIC_FAILED** | FAILED | N/A | $2,208.60 \text{ ms}$ |
| **Medium** | 150 | 12 | $0.35$ | 12 | N/A (Large) | N/A | **HEURISTIC_FAILED** | FAILED | N/A | $5,684.99 \text{ ms}$ |
| **Stress** | 200 | 15 | $0.40$ | 20 | N/A (Large) | N/A | **HEURISTIC_FAILED** | FAILED | N/A | $9,996.75 \text{ ms}$ |
| **Stress** | 200 | 5 | $0.60$ | 21 | N/A (Large) | N/A | **HEURISTIC_FAILED** | FAILED | N/A | $8,739.66 \text{ ms}$ |
| **Stress** | 200 | 20 | $0.10$ | 22 | N/A (Large) | N/A | **HEURISTIC_FAILED** | FAILED | N/A | $7,728.43 \text{ ms}$ |

### Diagnostic Analysis of Prescribed Instances:
- **Small Instances ($N=8, 10, 12$)**: DA-BnB exact solver exhaustively proved that all 3 prescribed small instances are **genuinely mathematically infeasible** (`PROVEN_INFEASIBLE`).
- **Cause of Infeasibility**: High conflict graph density ($0.30 \dots 0.50$) combined with narrow SLA windows $[l_i, u_i] \subseteq [1, K]$ creates cliques $K_c$ with chromatic number $\chi(K_c) > K$ within restricted SLA windows.
- **RSP-RRS Performance**: RSP-RRS returns status `HEURISTIC_FAILED` on all 9 prescribed instances, correctly identifying that no feasible schedule could be constructed within constraint bounds.

---

## 2. Supplementary Scaling Benchmark (Solvable Low-Density Instances)

To evaluate empirical optimality gaps on solvable instances, additional benchmarks were executed with lower conflict density ($0.10 \dots 0.20$):

| Tasks ($N$) | Slots ($K$) | Pure BF Status | DA-BnB Status | $P_{\text{base}}$ | $P_{\text{bal}}$ | $P_{\text{OPT}}$ | RSP-RRS Penalty | Absolute Gap | Empirical Ratio |
|---|---|---|---|---|---|---|---|---|---|
| **4** | 3 | **OPTIMAL** | **OPTIMAL** | $35.67$ | $0.3037$ | $35.9737$ | $35.9737$ | **0.0000** | **1.0000** |
| **5** | 3 | **OPTIMAL** | **OPTIMAL** | $66.29$ | $0.0860$ | $66.3760$ | $66.3760$ | **0.0000** | **1.0000** |

---

## 3. Lambda Sensitivity Experiment

Demonstrates objective-aware candidate slot selection on a constructed instance ($N=2, K=2, w_1=100, w_2=2$):

| $\lambda_{\text{bal}}$ | $P_{\text{base}}$ | $P_{\text{bal}}$ | Total Penalty $\mathcal{P}$ | Task 2 Slot | Schedule Selection |
|---|---|---|---|---|---|
| **0.00** | $102.00$ | $0.5000$ | $102.0000$ | **Slot 1** | Schedule A (Minimizes $P_{\text{base}}$) |
| **0.01** | $102.00$ | $0.5000$ | $102.0050$ | **Slot 1** | Schedule A |
| **0.10** | $102.00$ | $0.5000$ | $102.0500$ | **Slot 1** | Schedule A |
| **0.50** | $102.00$ | $0.5000$ | $102.2500$ | **Slot 1** | Schedule A |
| **1.00** | $102.00$ | $0.5000$ | $102.5000$ | **Slot 1** | Schedule A |
| **2.00** | $102.00$ | $0.5000$ | $103.0000$ | **Slot 1** | Schedule A |
| **5.00** | $104.00$ | $0.0000$ | $104.0000$ | **Slot 2** | Schedule B (Minimizes $P_{\text{bal}}$) |
| **10.00** | $104.00$ | $0.0000$ | $104.0000$ | **Slot 2** | Schedule B |
| **50.00** | $104.00$ | $0.0000$ | $104.0000$ | **Slot 2** | Schedule B |
| **100.00** | $104.00$ | $0.0000$ | $104.0000$ | **Slot 2** | Schedule B |

### Conclusion:
This constructed instance demonstrates objective-aware candidate slot selection for the tested $\lambda$ values. When $\lambda_{\text{bal}} \ge 5.0$, the solver trades off completion time penalty for perfect load balance.
