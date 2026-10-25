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
from collections.abc import Mapping


class RandomizerTrace:
    """Collects deterministic checkpoints for oracle and parity tests.

    The trace deliberately contains only JSON-serializable values or hashes of
    binary values. Large ROM data is represented by its SHA-256 digest.
    """

    def __init__(self):
        self.checkpoints = []
        self.patches = []

    def checkpoint(self, name: str, **data):
        self.checkpoints.append({"name": name, **data})

    def record_patches(self, patches: Mapping[int, bytes | bytearray | tuple]):
        manifest = []
        total_bytes = 0
        for offset in sorted(patches):
            patch_data = bytes(patches[offset])
            total_bytes += len(patch_data)
            manifest.append({
                "offset": offset,
                "length": len(patch_data),
                "sha256": hashlib.sha256(patch_data).hexdigest(),
            })
        self.patches.append({
            "count": len(manifest),
            "total_bytes": total_bytes,
            "entries": manifest,
        })

    def to_dict(self) -> dict:
        return {
            "checkpoints": self.checkpoints,
            "patch_sets": self.patches,
        }
