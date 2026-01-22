# Procedural Memory: STAC Manager Best Practices

## Development Workflow
- **Spec-First**: Always read `docs/spec/` before proposing designs.
- **TDD Pattern**: 
  1. Red (write failing test)
  2. Watch it fail (verify failure reason)
  3. Green (minimal implementation)
  4. Refactor (clean and optimize)
- **Granularity**: Keep tasks "bite-sized" (2-5 minutes) to ensure high-velocity, meaningful commits.

## Python Standards
- Use Python 3.12+ features (Generics, TypeVar, Structural Pattern Matching).
- Prefer readability and maintainability over complex "clever" one-liners.
- No mocks in end-to-end tests; use real or synthetic STAC data.
## Error Handling
- **Three-Tier Model**:
  1. **Tier 1: Fail Fast**: Configuration/startup errors (Abort workflow).
  2. **Tier 2: Step Out**: Item-level non-critical errors (Log to FailureCollector, continue pipeline).
  3. **Tier 3: Graceful Degradation**: Optional feature failures (Fallback safely with warning).
