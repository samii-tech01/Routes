from core.state import ErrandState

def evaluator_agent(state: ErrandState) -> ErrandState:
    """
    Eval Node: Evaluator Agent
    Validates the generated plan against hard constraints and dependencies.
    """
    print("Evaluator Agent: Validating plan constraints...")
    
    flags = []
    sequence = state.get("optimized_sequence", [])
    deps = state.get("dependency_graph", {})
    
    if not sequence:
        flags.append("No sequence generated.")
        return {"eval_flags": flags}
    
    # Check dependencies
    # If A depends on B, B must appear before A in the sequence.
    # state["dependency_graph"] format: { 'A': ['B'] } means A depends on B.
    for errand_id, depends_on_list in deps.items():
        if errand_id in sequence:
            idx_errand = sequence.index(errand_id)
            for dep in depends_on_list:
                if dep in sequence:
                    idx_dep = sequence.index(dep)
                    if idx_dep > idx_errand:
                        flags.append(f"Dependency violation: {errand_id} scheduled before its dependency {dep}.")
                else:
                    flags.append(f"Missing dependency: {dep} is not in the schedule but {errand_id} requires it.")
                    
    # In a full version, we'd also check arithmetic feasibility of travel times vs opening hours.
    
    if flags:
        print(f"Evaluator flagged issues: {flags}")
    else:
        print("Evaluator: Plan looks solid.")
        
    return {"eval_flags": flags}
