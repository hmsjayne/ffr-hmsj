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

import sys
from typing import Protocol


class ProgressReporter(Protocol):
    def update(self, stage: str, message: str) -> None:
        ...


class NullProgressReporter:
    def update(self, stage: str, message: str) -> None:
        pass


class PrintProgressReporter:
    def __init__(self, file=None):
        self.file = file if file is not None else sys.stdout

    def update(self, stage: str, message: str) -> None:
        print(f"[{stage}] {message}", file=self.file)
