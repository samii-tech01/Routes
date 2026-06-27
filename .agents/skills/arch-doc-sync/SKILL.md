---
name: arch-doc-sync
description: Regenerates architecture diagrams and documentation whenever agent roles or data flow change.
---

# Architecture Doc Sync Skill

## Usage Context
Use this skill to keep the documentation and architecture diagrams in sync with the codebase.

## Actions
1. Scan the `agents/` directory to identify active agents and their communication pathways.
2. Generate a Mermaid.js flowchart mapping the flow from User -> Orchestrator -> Specialist Agents -> Orchestrator.
3. Update `README.md` or a dedicated `ARCHITECTURE.md` file with the latest diagram and agent role descriptions.
