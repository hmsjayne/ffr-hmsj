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

"""Small abstraction over the randomizer's non-ROM data files.

The Python implementation reads from the checkout (or a PyInstaller bundle).
The TypeScript port will provide the same interface backed by imported assets.
Keeping this behind a protocol makes the randomizer core easier to test and
avoids sprinkling filesystem calls throughout the data loaders.
"""

from collections.abc import Mapping
from pathlib import Path
from typing import Protocol

from doslib.dos_utils import resolve_path


class DataSource(Protocol):
    def read_bytes(self, path: str) -> bytes:
        ...

    def read_text(self, path: str) -> str:
        ...

    def list_files(self, directory: str, suffix: str = "") -> list[str]:
        ...


class FileSystemDataSource:
    """Read data files from a checkout or a PyInstaller bundle."""

    def __init__(self, root: str | Path | None = None):
        self.root = Path(root) if root is not None else None

    def _path(self, path: str | Path) -> Path:
        candidate = Path(path)
        if candidate.is_absolute():
            return candidate
        if self.root is not None:
            return self.root / candidate
        return Path(resolve_path(str(candidate)))

    def read_bytes(self, path: str) -> bytes:
        return self._path(path).read_bytes()

    def read_text(self, path: str) -> str:
        return self._path(path).read_text(encoding="utf-8")

    def list_files(self, directory: str, suffix: str = "") -> list[str]:
        directory_path = self._path(directory)
        return sorted(
            path.name
            for path in directory_path.iterdir()
            if path.is_file() and path.name.endswith(suffix)
        )


class InMemoryDataSource:
    """Data source used by unit tests and future conformance vectors."""

    def __init__(self, files: Mapping[str, bytes | str]):
        self._files = {self._normalize(path): value for path, value in files.items()}

    @staticmethod
    def _normalize(path: str | Path) -> str:
        return Path(path).as_posix()

    def read_bytes(self, path: str) -> bytes:
        value = self._files[self._normalize(path)]
        return value.encode("utf-8") if isinstance(value, str) else value

    def read_text(self, path: str) -> str:
        value = self._files[self._normalize(path)]
        return value.decode("utf-8") if isinstance(value, bytes) else value

    def list_files(self, directory: str, suffix: str = "") -> list[str]:
        normalized_directory = self._normalize(directory).rstrip("/")
        files = []
        for path in self._files:
            pure_path = Path(path)
            if pure_path.parent.as_posix() == normalized_directory and pure_path.name.endswith(suffix):
                files.append(pure_path.name)
        return sorted(files)
