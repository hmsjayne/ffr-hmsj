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

"""Portable randomizer RNG.

The production randomizer uses xoshiro128** with a 128-bit state derived from
SHA-256 of the normalized seed. This file is intentionally self-contained so
the same algorithm can be implemented byte-for-byte in TypeScript.

This is not a cryptographic random number generator.
"""

import hashlib
import operator
import secrets
import struct

MASK32 = 0xFFFFFFFF
_SEED_DOMAIN = b"hmsjayne-rng-v1\x00"


def _rotl(value: int, count: int) -> int:
    return ((value << count) | (value >> (32 - count))) & MASK32


class RNG:
    def __init__(self, seed=None):
        self._state = [0, 0, 0, 0]
        if seed is None:
            seed = secrets.token_bytes(32)
        self.seed(seed)

    def seed(self, seed) -> None:
        if isinstance(seed, str):
            material = seed.encode("utf-8")
        elif isinstance(seed, (bytes, bytearray)):
            material = bytes(seed)
        elif isinstance(seed, int):
            material = str(seed).encode("ascii")
        else:
            raise TypeError("seed must be a string, bytes, or integer")

        digest = hashlib.sha256(_SEED_DOMAIN + material).digest()
        state = list(struct.unpack("<4I", digest[:16]))
        if state == [0, 0, 0, 0]:
            # xoshiro requires a non-zero state; this branch is effectively
            # unreachable for SHA-256 output but keeps the generator valid.
            state = [0x9E3779B9, 0x243F6A88, 0xB7E15162, 0xDEADBEEF]
        self._state = state

    def _next_u32(self) -> int:
        state = self._state
        result = _rotl((state[1] * 5) & MASK32, 7)
        result = (result * 9) & MASK32

        t = (state[1] << 9) & MASK32
        state[2] ^= state[0]
        state[3] ^= state[1]
        state[1] ^= state[2]
        state[0] ^= state[3]
        state[2] ^= t
        state[3] = _rotl(state[3], 11)

        state[0] &= MASK32
        state[1] &= MASK32
        state[2] &= MASK32
        state[3] &= MASK32
        return result

    def _randbelow(self, n: int) -> int:
        if n <= 0:
            raise ValueError("n must be greater than zero")
        if n > 0x100000000:
            raise ValueError("n must fit in 32 bits")
        if n == 1:
            return 0

        width = (n - 1).bit_length()
        while True:
            value = self._next_u32() >> (32 - width)
            if value < n:
                return value

    def randrange(self, start, stop=None, step=1) -> int:
        start = operator.index(start)
        step = operator.index(step)
        if stop is None:
            if step != 1:
                raise ValueError("step must be 1 when stop is not supplied")
            start, stop = 0, start
        else:
            stop = operator.index(stop)

        if step == 0:
            raise ValueError("step must not be zero")
        if step > 0:
            width = (stop - start + step - 1) // step
        else:
            width = (start - stop + (-step) - 1) // (-step)
        if width <= 0:
            raise ValueError("empty range for randrange()")
        return start + step * self._randbelow(width)

    def randint(self, a: int, b: int) -> int:
        return self.randrange(a, b + 1)

    def choice(self, sequence):
        size = len(sequence)
        if size == 0:
            raise IndexError("Cannot choose from an empty sequence")
        return sequence[self._randbelow(size)]

    def shuffle(self, sequence) -> None:
        for index in range(len(sequence) - 1, 0, -1):
            swap_index = self._randbelow(index + 1)
            sequence[index], sequence[swap_index] = sequence[swap_index], sequence[index]

    def sample(self, population, k: int):
        size = len(population)
        k = operator.index(k)
        if k < 0 or k > size:
            raise ValueError("sample larger than population or is negative")
        if k == 0:
            return []

        indices = list(range(size))
        for index in range(k):
            swap_index = index + self._randbelow(size - index)
            indices[index], indices[swap_index] = indices[swap_index], indices[index]
        return [population[indices[index]] for index in range(k)]

    def random(self) -> float:
        high = self._next_u32() >> 5
        low = self._next_u32() >> 6
        return (high * 67108864.0 + low) / 9007199254740992.0
