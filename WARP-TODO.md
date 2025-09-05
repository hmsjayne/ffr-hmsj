# WARP-TODO.md

This file contains implementation tasks and roadmaps for ongoing development in the Final Fantasy HMS Jayne randomizer.

## Next-Generation Event System (`new_events/`)

The `new_events/` directory contains work toward a modernized event system to replace `event/e2s.py`. The goal is to create Python-like scripts that are easier to understand and maintain than the current assembly-style event code.

### Current State
- ✅ **Event Parsing**: Can parse events by their IDs
- ✅ **Basic CFG Construction**: Builds control flow graphs from parsed instructions
- ✅ **Control Flow Detection**: Can identify basic control flows in the bytecode
- ✅ **Return Instruction Handling**: CFG properly handles return instructions as block terminators
- ⚠️ **CFG Data Return**: Returns data about control flows but without annotations

### Implementation Roadmap

#### Phase 1: CFG Annotation (In Progress)
- [ ] **Annotate CFG with Loop Detection**
  - Identify while loops, for loops, and other iterative structures
  - Mark loop entry points, conditions, and exit points
  - Handle nested loop scenarios

- [ ] **Annotate CFG with Conditional Logic**
  - Detect if/then/else statement patterns
  - Identify switch/case-like structures
  - Mark conditional branches and merge points

- [ ] **Advanced Control Flow Annotation**
  - Function call detection and mapping
  - Return statement identification  
  - Exception/error handling patterns (if applicable)

#### Phase 2: AST Generation
- [ ] **CFG to AST Transformation**
  - Convert annotated CFG nodes to AST nodes
  - Preserve semantic meaning during transformation
  - Handle complex control flow edge cases

- [ ] **AST Optimization**
  - Simplify redundant branches
  - Optimize loop structures
  - Clean up unnecessary intermediate variables

#### Phase 3: Python-like Script Generation
- [ ] **Code Generation Framework**
  - Design Python-like syntax for event scripts
  - Create templates for common event patterns
  - Ensure generated code matches project style

- [ ] **Script Output**
  - Generate readable Python-like event scripts
  - Include comments and documentation in generated code
  - Maintain mapping between original bytecode and generated script

- [ ] **Validation and Testing**
  - Verify generated scripts produce equivalent bytecode
  - Create test suite for event transformation pipeline
  - Performance testing for large event files

#### Phase 4: Integration and Migration
- [ ] **Replace `event/e2s.py`**
  - Integrate new system with existing randomizer pipeline
  - Update all references to old event system
  - Maintain backward compatibility during transition

- [ ] **Developer Tools**
  - Create utilities for viewing CFGs
  - Build debugging tools for script generation
  - Documentation for working with new event system

### Technical Considerations

#### Architecture Notes
- The new system should maintain compatibility with existing ROM manipulation workflows
- Generated Python-like scripts should integrate with the current build system
- CFG representation should be serializable for debugging and analysis

#### Testing Strategy
- Unit tests for each phase of the pipeline (parsing → CFG → AST → script generation)
- Integration tests with real game event data
- Regression tests to ensure no functionality loss during migration

#### Performance Goals
- Event parsing should be faster than current `e2s.py`
- CFG construction should handle large event files efficiently
- Generated scripts should be human-readable and maintainable

### Getting Started

To contribute to the next-generation event system:

1. **Understand Current State**: Explore `new_events/` directory structure
2. **Review CFG Implementation**: Examine existing control flow graph construction
3. **Identify Patterns**: Look at `event/e2s.py` to understand current limitations
4. **Start with Annotation**: Begin by adding annotations to existing CFG nodes

### Related Files and Directories

- `new_events/`: New event system implementation
- `event/e2s.py`: Current event system to be replaced
- `event/easm.py`: Event assembler (may need integration)
- `event/epp.py`: Event preprocessor (may need integration)
- `scripts/`: Will contain generated Python-like event scripts
