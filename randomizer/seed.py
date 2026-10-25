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
import secrets
import tomllib

SEED_MIN_LENGTH = 1
SEED_MAX_LENGTH = 32


class InvalidSeedError(ValueError):
    pass


def normalize_seed(seed: str) -> str:
    if not isinstance(seed, str):
        raise InvalidSeedError("seed must be a string")

    normalized = seed.strip()
    if len(normalized) < SEED_MIN_LENGTH:
        raise InvalidSeedError("seed must not be empty")
    if len(normalized) > SEED_MAX_LENGTH:
        raise InvalidSeedError(f"seed must be at most {SEED_MAX_LENGTH} characters")
    if any(ord(char) < 0x20 or ord(char) > 0x7E for char in normalized):
        raise InvalidSeedError("seed must contain printable ASCII characters only")
    return normalized


def seed_bytes(seed: str) -> bytes:
    return hashlib.sha256(normalize_seed(seed).encode("utf-8")).digest()


def seed_checksum(seed: str) -> str:
    """A short display-only checksum. Never use this as the seed itself."""
    return seed_bytes(seed).hex()[:10]


def generate_seed(data_source=None, rng=None) -> str:
    """Generate a short, readable seed phrase.

    Falls back to a random hex string if the word list is unavailable or cannot
    produce a phrase within the seed length limit.
    """
    if rng is None:
        rng = secrets.SystemRandom()

    try:
        if data_source is None:
            from doslib.data_source import FileSystemDataSource

            data_source = FileSystemDataSource()
        seed_data = tomllib.loads(data_source.read_text("static/seed_data.toml"))
        titles = seed_data["titles"]
        prefixes = seed_data["prefixes"]
        creatures = seed_data["creatures"]
    except (KeyError, OSError, tomllib.TOMLDecodeError):
        return secrets.token_hex(8)

    for _ in range(100):
        candidate = f"{rng.choice(titles)} {rng.choice(prefixes)} {rng.choice(creatures)}"
        if SEED_MIN_LENGTH <= len(candidate) <= SEED_MAX_LENGTH:
            return candidate

    return secrets.token_hex(8)
