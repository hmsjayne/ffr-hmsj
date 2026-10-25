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

from collections.abc import Iterator, MutableMapping


class PatchConflictError(RuntimeError):
    pass


class PatchSet(MutableMapping[int, bytes]):
    """A ROM patch collection that refuses to silently overwrite entries."""

    def __init__(self, patches=None):
        self._patches: dict[int, bytes] = {}
        self._sources: dict[int, str] = {}
        if patches is not None:
            self.update(patches)

    def add(self, offset: int, data, source: str | None = None) -> None:
        if offset in self._patches:
            previous = self._sources.get(offset, "unknown")
            raise PatchConflictError(
                f"Multiple patches target {hex(offset)}: {previous} vs {source or 'unknown'}"
            )
        self._patches[offset] = bytes(data)
        self._sources[offset] = source or "unknown"

    def update(self, other=(), source: str | None = None, **kwargs) -> None:
        for offset, data in dict(other).items():
            self.add(offset, data, source)
        for offset, data in kwargs.items():
            self.add(offset, data, source)

    def __setitem__(self, offset: int, data) -> None:
        self.add(offset, data)

    def __getitem__(self, offset: int) -> bytes:
        return self._patches[offset]

    def __delitem__(self, offset: int) -> None:
        del self._patches[offset]
        self._sources.pop(offset, None)

    def __iter__(self) -> Iterator[int]:
        return iter(self._patches)

    def __len__(self) -> int:
        return len(self._patches)

    def to_dict(self) -> dict[int, bytes]:
        return dict(self._patches)
