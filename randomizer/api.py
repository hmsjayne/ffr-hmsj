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

from randomizer.options import ALGORITHM_VERSION, DEFAULT_OPTIONS, RandomizerOptions
from randomizer.randomize import randomize
from randomizer.seed import normalize_seed
from randomizer.trace import RandomizerTrace


@dataclass(frozen=True)
class RandomizerResult:
    """The result of a single randomizer run."""

    rom_data: bytes
    seed: str
    options: RandomizerOptions
    base_rom_sha256: str
    trace: RandomizerTrace | None = None

    @property
    def options_short(self) -> str:
        return self.options.short_code()

    @property
    def rom_sha256(self) -> str:
        return hashlib.sha256(self.rom_data).hexdigest()

    @property
    def rom_size(self) -> int:
        return len(self.rom_data)

    def to_metadata(self) -> dict:
        """Return the stable, JSON-serializable part of the result."""
        metadata = {
            "algorithm_version": ALGORITHM_VERSION,
            "seed": self.seed,
            "options": self.options.to_dict(),
            "options_short": self.options_short,
            "base_rom_sha256": self.base_rom_sha256,
            "rom_sha256": self.rom_sha256,
            "rom_size": self.rom_size,
        }
        if self.trace is not None:
            metadata["trace"] = self.trace.to_dict()
        return metadata


def randomize_rom(rom_data: bytes | bytearray,
                  seed: str,
                  options: RandomizerOptions | None = None,
                  data_source=None,
                  collect_trace: bool = False,
                  progress=None) -> RandomizerResult:
    """Run the randomizer through the stable programmatic entry point."""
    if not isinstance(rom_data, (bytes, bytearray)):
        raise TypeError("rom_data must be bytes or bytearray")
    normalized_seed = normalize_seed(seed)

    rom_bytes = bytes(rom_data)
    active_options = options if options is not None else DEFAULT_OPTIONS
    trace = RandomizerTrace() if collect_trace else None
    randomized = randomize(bytearray(rom_bytes), normalized_seed, active_options,
                           data_source=data_source, trace=trace, progress=progress)

    return RandomizerResult(
        rom_data=bytes(randomized),
        seed=normalized_seed,
        options=active_options,
        base_rom_sha256=hashlib.sha256(rom_bytes).hexdigest(),
        trace=trace,
    )
