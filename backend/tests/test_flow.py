"""
End-to-End Flow Test for Errand Brain Agent Society
=====================================================
Run with: python tests/test_flow.py

This script walks through the FULL agent pipeline step-by-step
with a realistic scenario so you can see each agent's output.

FLOW:
  User Input
      |
      v
  [Parser Agent]        -- extracts structured Errand objects
      |
      v
  [Memory Agent]        -- (future) injects preferred locations from DB
      |
      +---------------------------+---------------------------+
      v                          v                           v
  [Geo Agent]           [Temporal Agent]           [Dependency Agent]
  (minimize distance)   (meet deadlines/hours)     (obey prerequisites)
      |                          |                           |
      +---------------------------+---------------------------+
                                 |
                                 v
                        [Orchestrator Agent]
                        (negotiates best plan)
                                 |
                                 v
                           FINAL PLAN TEXT
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.state import ErrandState, Errand
from core.config import validate_config
from agents.parser import parser_agent
from agents.memory_agent import memory_agent
from agents.geo_clustering import geo_clustering_agent
from agents.temporal_constraint import temporal_constraint_agent
from agents.dependency import dependency_agent
from agents.orchestrator import orchestrator_agent

# ── Helpers ──────────────────────────────────────────────────────────────────

DIVIDER = "\n" + "=" * 60 + "\n"

def section(title: str):
    print("\n" + "-" * 60)
    print("  " + title)
    print("-" * 60)

def print_errands(errands):
    for e in errands:
        print(f"  [{e.id}] {e.description}")
        print(f"        type      : {e.errand_type}")
        print(f"        location  : {e.resolved_location or e.preferred_location or '—'}")
        print(f"        time      : {e.time_constraint or '—'}")
        print(f"        depends on: {e.dependencies or '—'}")

def print_proposals(proposals):
    for p in proposals:
        print(f"\n  Agent      : {p.agent_name}")
        print("  Sequence   : " + " -> ".join(p.proposed_sequence))
        print(f"  Penalty    : {p.score_penalty}")
        print(f"  Rationale  : {p.rationale[:120]}...")

# ── Scenario ─────────────────────────────────────────────────────────────────

TEST_INPUT = (
    "I need to: "
    "1) pick up a package from the post office (they close at 5pm), "
    "2) buy groceries at the supermarket, "
    "3) get cash from the ATM before the supermarket because they only take cash, "
    "4) pick up my prescription from the pharmacy (closes at 6pm). "
    "The post office and pharmacy are on the same side of town."
)

# ── Runner ────────────────────────────────────────────────────────────────────

def run():
    print(DIVIDER)
    print("  ERRAND BRAIN — Agent Society Flow Test")
    print(DIVIDER)

    validate_config()

    # Build initial state matching our new schema
    state: ErrandState = {
        "user_input": TEST_INPUT,
        "errands": [],
        "proposals": [],
        "final_plan_sequence": [],
        "final_plan_text": "",
        "explanation_trace": ""
    }

    print(f"INPUT:\n  {TEST_INPUT}\n")

    # ── STEP 1: Parser Agent ──────────────────────────────────────────────────
    section("STEP 1 / 6 — Parser Agent  (extract errands)")
    parser_output = parser_agent(state)
    state.update(parser_output)
    print(f"  Extracted {len(state['errands'])} errands:\n")
    print_errands(state["errands"])

    if not state["errands"]:
        print("\n  ✗ Parser returned no errands. Aborting.")
        return

    # ── STEP 2: Memory Agent ──────────────────────────────────────────────────
    section("STEP 2 / 6 — Memory Agent  (inject preferred locations)")
    memory_output = memory_agent(state)
    state.update(memory_output)
    print("  Memory agent ran (DB not wired yet — pass-through).")

    # ── STEP 3: Geo-Clustering Agent ──────────────────────────────────────────
    section("STEP 3 / 6 — Geo-Clustering Agent  (minimize distance)")
    geo_output = geo_clustering_agent(state)
    state.update(geo_output)
    print_proposals(state["proposals"])

    # ── STEP 4: Temporal-Constraint Agent ─────────────────────────────────────
    section("STEP 4 / 6 — Temporal-Constraint Agent  (meet deadlines)")
    temporal_output = temporal_constraint_agent(state)
    state.update(temporal_output)
    print_proposals([state["proposals"][-1]] if state["proposals"] else [])

    # ── STEP 5: Dependency Agent ───────────────────────────────────────────────
    section("STEP 5 / 6 — Dependency Agent  (obey prerequisites)")
    dep_output = dependency_agent(state)
    state.update(dep_output)
    print_proposals([state["proposals"][-1]] if state["proposals"] else [])

    # ── STEP 6: Orchestrator ────────────────────────────────────────────────────
    section("STEP 6 / 6 — Orchestrator  (negotiate best plan)")
    print(f"\n  Received {len(state['proposals'])} proposals to evaluate...\n")
    orch_output = orchestrator_agent(state)
    state.update(orch_output)

    # ── Final Output ────────────────────────────────────────────────────────────
    print(DIVIDER)
    print("  FINAL PLAN")
    print(DIVIDER)
    print(state.get("final_plan_text", "No plan generated."))
    print(DIVIDER)

if __name__ == "__main__":
    run()
