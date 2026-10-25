# Golden randomizer baseline

This directory contains hash-only baselines for the Python reference
implementation. The base ROM is **not** stored in the repository.

## Generate the baseline

```bash
python tools/generate_goldens.py --rom /path/to/ff1-dos.gba
```

The manifest records:

- base ROM SHA-256 and size
- randomizer flags and seed for each case
- randomized ROM hash and size
- IPS patch hash and size
- compact placement/patch/data-load trace hashes
- hashes of the data, script, patch, and ASP assets used by the randomizer

## Run parity tests

```bash
HMSJAYNE_ROM=/path/to/ff1-dos.gba pytest tests/integration/test_golden.py
```

The integration tests validate the supplied ROM against the recorded base hash
before running any cases. Without `HMSJAYNE_ROM`, the unit tests still run and
the ROM parity cases are skipped.

When the randomizer's behavior is intentionally changed, regenerate this file
in a dedicated commit and review the changed cases.
