# Specification Writing Guide: Detail Levels

**Status**: Adopted Standard  
**Purpose**: Define the appropriate level of abstraction for STAC Manager technical specifications.

---

## Overview

To create specifications that serve as effective blueprints without over-constraining the implementation, we adopt a **3-Tier Detail Strategy**. All technical documentation should adhere to these tiers based on the type of component being described.

---

## Tier 1: Exact Contracts (Strict)

**Applies to**: Public Interfaces, Module Protocols, Data Schemas, Config Structures, Error Hierarchies.

**Requirement**: These must be specified **exactly** as they will appear in the code (signatures, types, field names).

**Example (Protocol)**:
```python
# CORRECT (Tier 1)
class ModuleProtocol(Protocol):
    async def execute(self, context: WorkflowContext) -> Any: ...

# INCORRECT (Too Vague)
# "Modules should have an execute method that takes context."
```

**Rationale**: These are the "hard boundaries" between components. Ambiguity here causes integration failures.

---

## Tier 2: Algorithmic Guidance (Logic)

**Applies to**: Critical Logic Flows, State Machines, Complex Algorithms (e.g., DAG Resolution, Rate Limiting Strategy).

**Requirement**: Describe the **steps and logic** clearly, often using "Pseudocode" or numbered lists. Do **not** dictate the exact internal implementation (variable names, helper functions) unless critical.

**Best Practice for Pseudocode**:
- Use Pythonic syntax for readability but ignore import/boilerplate.
- Focus on control flow (`if`, `for`, `while`) and critical calls.
- Abstract away implementation details (e.g., `db.save()` instead of full SQL/connection logic).

**Example (DAG Algo)**:
```python
# CORRECT (Tier 2 - Algorithmic Guidance)
def resolve_dependencies(steps):
    graph = build_graph(steps)
    sorted_nodes = kahn_sort(graph)
    if detect_cycles(graph):
        raise ConfigurationError("Cycle detected")
    return sorted_nodes
```

**Rationale**: Ensures the *behavior* is correct while letting the developer choose the best library or implementation pattern.

---

## Tier 3: Conceptual Only (Flexible)

**Applies to**: Internal Component Design, Performance Optimizations, Library Choices, Private Methods.

**Requirement**: Describe **what** needs to be achieved and **why**, but leave the **how** completely to the implementer.

**Example (Retry Logic)**:
- **Spec**: "The system must implement exponential backoff with jitter to handle intermittent API failures."
- **NOT**: "Use the `tenacity` library with the `wait_random_exponential` decorator."

**Rationale**: Avoiding over-specification allows developers to refactor internals without breaking the "Spec" compliance. It prevents the spec from becoming stale immediately.

---

## Summary Matrix

| Component Type | Detail Tier | What to Specify | What to Avoid |
| :--- | :--- | :--- | :--- |
| **Inter-Module APIs** | **Tier 1 (Exact)** | Exact signatures, Types, Exceptions | Vague naming |
| **Data Models (JSON/Dict)** | **Tier 1 (Exact)** | Field names, Types, Nullability | "Similar to..." |
| **Critical Workflows** | **Tier 2 (Logic)** | Step-by-step logic, Flowcharts | Boilerplate code |
| **Internal Implementation** | **Tier 3 (Concept)** | Requirements, Constraints | Internal class names |
| **Performance Tuning** | **Tier 3 (Concept)** | Goals, Strategies | Magic numbers (unless strict) |
