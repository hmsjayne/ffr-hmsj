# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

Final Fantasy: HMS Jayne is a proof-of-concept randomizer for Final Fantasy I: Dawn of Souls (Nintendo GameBoy Advance). The randomizer shuffles key items, NPCs, magic levels, and treasure while maintaining logical progression through Answer Set Programming (ASP) constraint solving.

## Development Commands

### Dependencies Installation
```bash
pip install -r requirements.txt
```

### Running the Randomizer
```bash
# Command line interface
python randomize.py <rom_file.gba> [options]

# GUI interface  
python randomize-gui.py

# Web interface
python flask-app.py
```

### Testing
```bash
# Run all tests
PYTHONPATH=. python -m unittest discover event/tests/ -v

# Run specific test module
PYTHONPATH=. python -m unittest event.tests.test_codegen -v
PYTHONPATH=. python -m unittest event.tests.test_epp -v
```

Note: Some tests in `test_easm.py` are currently failing due to API changes in the parse function.

### Creating IPS Patches
```bash
# Generate an IPS patch instead of a new ROM
python randomize.py <rom_file.gba> --patch
```

## Architecture Overview

### Core Libraries

**doslib/**: Dawn of Souls library - Core ROM manipulation
- `rom.py`: Central ROM class for reading/writing GBA ROM data, pointer/offset conversion
- `classes.py`: Job class data structures and manipulation
- `enemy.py`: Enemy stats, encounters, and formation data
- `item.py`, `items.py`: Item definitions and inventory management
- `maps.py`: Map data, NPCs, treasure chests, and map features
- `spells.py`: Magic system and spell data
- `event.py`: Event system integration and text blocks

**randomizer/**: Randomization logic
- `randomize.py`: Main randomization orchestrator, coordinates all randomization systems
- `clingo.py`: Interface to Clingo ASP solver for key item placement
- `placement.py`: Key item placement logic and validation
- `treasure.py`: Treasure chest randomization
- `bossshuffle.py`: Boss encounter randomization
- `flags.py`: Configuration flags and encoding/decoding

**event/**: Event bytecode assembly system
- `easm.py`: Event assembler for converting assembly to bytecode
- `epp.py`: Event preprocessor with macro support
- `tokens.py`: Tokenization and parsing utilities

### Key Item Placement System

The randomizer uses **Clingo** (Answer Set Programming) to solve key item placement constraints:

1. **ASP Files** (`asp/`): Define placement rules and constraints
   - `KeyItemDataShip.lp`: Defines items, locations, and accessibility rules
   - `KeyItemSolvingShip.lp`: Core constraint logic ensuring all items remain accessible

2. **Process Flow**:
   - Clingo solver generates valid key item placements
   - NPCs are moved to new locations but retain their original rewards
   - Example: If King of Cornelia becomes Smyth the Dwarf, rescuing the NPC kidnapped by Garland will yield Excalibur (Smyth's original reward)

### ROM Structure Understanding

- **Pointer System**: Uses GBA pointer format (0x8000000 + ROM offset)
- **Data Streams**: Most game data accessed through `InputStream`/`OutputStream`
- **Patch Application**: Supports both direct ROM modification and IPS patch generation
- **Free Space Management**: Manages unused ROM space for new data through `FreeBlock` system

### Event System

Custom bytecode system for game events:
- Assembly-like syntax compiled to game bytecode
- Preprocessor supports macros and conditional compilation  
- Used for modifying NPC dialogues and interactions

**Next-Generation Event System** (`new_events/`):
- Replacement for `event/e2s.py` with more robust parsing
- Parses events by ID and builds control flow graphs (CFG)
- Can identify basic control flows but CFG annotation is in progress
- Goal: Generate Python-like scripts from CFG via AST transformation

## Development Patterns

### ROM Data Modification Pattern
```python
# Load data from ROM
data_stream = rom.open_bytestream(offset, size)
objects = [DataClass(data_stream) for _ in range(count)]

# Modify objects
for obj in objects:
    obj.property = new_value

# Write back to ROM
output_stream = OutputStream()
for obj in objects:
    obj.write(output_stream)
patches[offset] = output_stream.get_buffer()
```

### Adding New Randomization Features
1. Define data structures in `doslib/`
2. Add loading/saving functions in `randomizer/randomize.py`
3. Implement randomization logic in dedicated module
4. Add configuration flags in `flags.py`
5. Update command-line and GUI interfaces

### Testing Event Code
The event system has unit tests but some are currently failing. When working with event assembly:
- Test preprocessor functionality with `test_epp.py` 
- Test code generation with `test_codegen.py`
- The `test_easm.py` tests need fixing for the current parse API

### Constraint Solving for Key Items
When modifying key item logic:
- Update ASP files in `asp/` directory
- Test accessibility logic carefully - items must remain obtainable
- The solver ensures NPCs can be reached with available key items
- Bottle is hardcoded to caravan location due to complexity

## File Structure Notes

- `data/`: TSV files containing game data modifications and patches, including `KeyItemPlacement.tsv` with NPC and location ID mappings
- `static/`: Web interface assets and GUI resources  
- `stream/`: Low-level stream I/O utilities (referenced but not in main directory)
- `new_events/`: Next-generation event system to replace `event/e2s.py` - parses events by ID, builds control flow graphs, and aims to generate Python-like scripts
- `scripts/`: Source code for events in the game. Compiled by the Event bytecode assembly system
- `patches/`: Binary patches for making changes to the game code

## Dependencies

- `clingo~=5.7.1`: Answer Set Programming solver for key item placement
- `flask~=2.2.2`: Web interface framework
- `lark~=1.2.2`: Parser toolkit used in event system
- `ips-util~=1.0`: IPS patch file utilities
- `pillow~=10.4.0`: Image processing for GUI
- `pyinstaller~=6.9.0`: For creating standalone executables
