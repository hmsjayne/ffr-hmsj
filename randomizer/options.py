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

from dataclasses import asdict, dataclass, fields

ALGORITHM_VERSION = 4

MIN_XP_RATE_PERCENT = 50
MAX_XP_RATE_PERCENT = 500
XP_RATE_STEP = 10
DEFAULT_XP_RATE_PERCENT = 150

PUBLIC_FIELDS = (
    "shuffle_key_items",
    "randomize_shops",
    "randomize_treasure",
    "randomize_starting_gear",
    "randomize_bosses",
    "new_item_distribution",
    "fiend_ribbons",
    "xp_rate_percent",
)


@dataclass(frozen=True)
class RandomizerOptions:
    shuffle_key_items: bool = True
    randomize_shops: bool = True
    randomize_treasure: bool = True
    randomize_starting_gear: bool = True
    randomize_bosses: bool = True
    new_item_distribution: bool = False
    fiend_ribbons: bool = False
    xp_rate_percent: int = DEFAULT_XP_RATE_PERCENT
    debug: bool = False

    def __post_init__(self):
        for field in fields(self):
            value = getattr(self, field.name)
            if field.name == "xp_rate_percent":
                if isinstance(value, bool) or not isinstance(value, int):
                    raise TypeError("xp_rate_percent must be an integer")
                if value < MIN_XP_RATE_PERCENT or value > MAX_XP_RATE_PERCENT:
                    raise ValueError(
                        f"xp_rate_percent must be between {MIN_XP_RATE_PERCENT} and {MAX_XP_RATE_PERCENT}"
                    )
                if value % XP_RATE_STEP != 0:
                    raise ValueError(f"xp_rate_percent must be a multiple of {XP_RATE_STEP}")
            elif not isinstance(value, bool):
                raise TypeError(f"{field.name} must be a boolean")

    def public_dict(self) -> dict:
        return {name: getattr(self, name) for name in PUBLIC_FIELDS}

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, values: dict) -> "RandomizerOptions":
        names = {field.name for field in fields(cls)}
        unknown = set(values) - names
        if unknown:
            raise ValueError(f"Unknown option(s): {', '.join(sorted(unknown))}")

        data = asdict(cls())
        data.update(values)
        return cls(**data)

    def short_code(self) -> str:
        parts = []
        if self.shuffle_key_items:
            parts.append("K")
        if self.randomize_shops:
            parts.append("S")
        if self.randomize_treasure:
            parts.append("T")
        if self.randomize_starting_gear:
            parts.append("G")
        if self.randomize_bosses:
            parts.append("B")
        if self.new_item_distribution:
            parts.append("Ni")
        if self.fiend_ribbons:
            parts.append("R")
        return "".join(parts) + f"Xp{self.xp_rate_percent}"


DEFAULT_OPTIONS = RandomizerOptions()
