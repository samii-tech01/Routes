---
name: negotiation-protocol
description: Defines the deterministic conflict-resolution methodology for the Orchestrator to score proposals and break ties.
---

# Negotiation Protocol: Agent Society

This skill defines the exact logic the Orchestrator agent uses to resolve conflicts between the three specialist agents (Geo-Clustering, Temporal-Constraint, Dependency). This protocol acts as the "Non-trivial Logic" evidence for the hackathon judges.

## 1. Core Principles
The Agent Society must produce a single, globally optimal route plan. The Orchestrator does not generate plans from scratch; it evaluates and merges the overlapping (and often conflicting) proposals from specialists.

## 2. Constraint Hierarchy

### Tier 1: Hard Constraints (VETO POWER)
If any of these are violated, the proposal is **immediately rejected**.
- **Dependency Rules**: e.g., "Must pick up cake before going to the party."
- **Hard Deadlines**: e.g., "Doctor's appointment strictly at 3:00 PM."
- **Operating Hours**: e.g., "Pharmacy closes at 5:00 PM."

### Tier 2: Soft Constraints (PENALTY SYSTEM)
If these are violated, the proposal incurs a penalty score.
- **Preferred Time Windows**: e.g., "Prefer to do groceries in the morning." (Penalty: 10 pts)
- **Minimizing Drive Time**: (Penalty: 1 pt per minute of extra drive time compared to theoretical shortest path).

## 3. The Scoring Algorithm
The Orchestrator must use the following deterministic formula to evaluate valid proposals:

```text
Base Score = 1000

# Penalties
Total Score = Base Score
  - (Minutes of extra drive time * 1)
  - (Missed preferred time windows * 10)
  - (Context switching / Zig-zagging penalty * 5)
```

## 4. Resolution Loop (LangGraph Implementation)
1. **Gather Proposals**: Orchestrator queries Geo, Temporal, and Dependency agents in parallel.
2. **First Pass Evaluation**: Apply Tier 1 hard constraints. Discard invalid paths.
3. **Scoring**: Apply Tier 2 scoring to remaining paths.
4. **Tie-Breaking**: 
   - If two paths have identical scores, select the path that finishes all errands earliest in the day.
   - If still tied, select the path with the fewest total miles driven.
5. **Final Output**: The Orchestrator outputs the chosen sequence alongside an "Explanation Trace" detailing the scores of the top 2 proposals to prove its reasoning to the user (and judges).
