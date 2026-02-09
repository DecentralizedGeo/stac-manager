# StacManager System Visualization

This diagram illustrates how the `StacManager` orchestrator is instantiated, builds the pipeline, and executes the data flow through the requested steps: `ingest -> apply extension -> update -> validate -> output`.

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant SM as StacManager
    participant CFG as Config/DAG
    participant CTX as WorkflowContext
    participant MOD as Modules (Generic)
    participant DATA as CTX.data (Store)

    Note over User, SM: 1. Instantiation & Setup
    User->>SM: __init__(config)
    SM->>SM: Validate Configuration

    User->>SM: execute()
    activate SM
    
    SM->>CTX: _init_context(config)
    activate CTX
    CTX-->>SM: context initialized (empty data)
    deactivate CTX

    SM->>CFG: build_dag(steps)
    activate CFG
    Note right of CFG: Resolves dependencies:<br/>ingest -> ext -> update -> validate -> output
    CFG-->>SM: execution_levels = [[ingest], [ext], [update], [validate], [output]]
    deactivate CFG

    Note over SM, DATA: 2. Pipeline Execution (Level by Level)

    %% LEVEL 1: INGEST
    rect rgb(255, 250, 240)
    Note right of SM: Level 1: Ingest (Source)
    SM->>MOD: _import_module("IngestModule")
    SM->>MOD: __init__(step_config)
    SM->>MOD: fetch(context)
    activate MOD
    MOD-->>SM: yield Stream[Item]
    deactivate MOD
    SM->>DATA: Store "ingest": Stream[Item]
    end

    %% LEVEL 3: APPLY EXTENSION
    rect rgb(240, 255, 240)
    Note right of SM: Level 3: Apply Extension (Modifier)
    SM->>MOD: _import_module("ExtensionModule")
    SM->>MOD: __init__(step_config)
    SM->>DATA: Get input from "ingest"
    DATA-->>SM: Stream[Item]
    
    loop For each item in stream
        SM->>MOD: modify(item, context)
        MOD-->>SM: Modified Item
    end
    
    SM->>DATA: Store "apply_extension": Stream[Item]
    end

    %% LEVEL 4: UPDATE
    rect rgb(255, 240, 255)
    Note right of SM: Level 4: Update (Modifier)
    SM->>MOD: _import_module("UpdateModule")
    SM->>MOD: __init__(step_config)
    SM->>DATA: Get input from "apply_extension"
    DATA-->>SM: Stream[Item]
    
    loop For each item
        SM->>MOD: modify(item, context)
        MOD-->>SM: Updated Item
    end
    
    SM->>DATA: Store "update": Stream[Item]
    end

    %% LEVEL 5: VALIDATE
    rect rgb(240, 255, 255)
    Note right of SM: Level 5: Validate (Modifier/Check)
    SM->>MOD: _import_module("ValidateModule")
    SM->>MOD: __init__(step_config)
    SM->>DATA: Get input from "update"
    
    loop For each item
        SM->>MOD: modify(item, context)
        Note left of MOD: Log failure to FailureCollector<br/>if invalid, else return Item
        MOD-->>SM: Validated Item (or None)
    end
    
    SM->>DATA: Store "validate": Stream[Item]
    end

    %% LEVEL 6: OUTPUT
    rect rgb(255, 255, 240)
    Note right of SM: Level 6: Output (Bundler)
    SM->>MOD: _import_module("OutputModule")
    SM->>MOD: __init__(step_config)
    SM->>DATA: Get input from "validate"
    
    loop For each item
        SM->>MOD: bundle(item, context)
        Note left of MOD: Writes to disk/store
    end
    
    SM->>MOD: finalize(context)
    activate MOD
    MOD-->>SM: OutputResult (Manifest)
    deactivate MOD
    SM->>DATA: Store "output": OutputResult
    end

    Note over User, SM: 3. Finalization
    SM->>SM: Generate WorkflowResult (Summary, Failures)
    SM-->>User: WorkflowResult
    deactivate SM
```
