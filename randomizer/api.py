#  Copyright 2026 HMS Jayne contributors
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

import hashlib
from dataclasses import dataclass

from randomizer.flags import Flags
from randomizer.randomize import randomize
from randomizer.trace import RandomizerTrace


@dataclass(frozen=True)
class RandomizerResult:
    """The result of a single randomizer run."""

    rom_data: bytes
    seed: str
    flags: Flags
    base_rom_sha256: str
    trace: RandomizerTrace | None = None

    @property
    def flags_encoded(self) -> str:
        return self.flags.encode()

    @property
    def rom_sha256(self) -> str:
        return hashlib.sha256(self.rom_data).hexdigest()

    @property
    def rom_size(self) -> int:
        return len(self.rom_data)

    def to_metadata(self) -> dict:
        """Return the stable, JSON-serializable part of the result."""
        metadata = {
            "seed": self.seed,
            "flags": dict(vars(self.flags)),
            "flags_encoded": self.flags_encoded,
            "base_rom_sha256": self.base_rom_sha256,
            "rom_sha256": self.rom_sha256,
            "rom_size": self.rom_size,
        }
        if self.trace is not None:
            metadata["trace"] = self.trace.to_dict()
        return metadata


def randomize_rom(rom_data: bytes | bytearray,
                  seed: str,
                  flags: Flags | None = None,
                  collect_trace: bool = False) -> RandomizerResult:
    """Run the randomizer through the stable programmatic entry point.

    This deliberately does not normalize seeds or flags yet; Phase 2 will make
    those canonical. It exists so the CLI, oracle, and future TypeScript port
    all exercise the same path.
    """
    if not isinstance(rom_data, (bytes, bytearray)):
        raise TypeError("rom_data must be bytes or bytearray")
    if not isinstance(seed, str):
        raise TypeError("seed must be a string")

    rom_bytes = bytes(rom_data)
    active_flags = flags if flags is not None else Flags()
    trace = RandomizerTrace() if collect_trace else None
    randomized = randomize(bytearray(rom_bytes), seed, active_flags, trace=trace)

    return RandomizerResult(
        rom_data=bytes(randomized),
        seed=seed,
        flags=active_flags,
        base_rom_sha256=hashlib.sha256(rom_bytes).hexdigest(),
        trace=trace,
    )
