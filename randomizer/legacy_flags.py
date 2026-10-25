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

import re
from dataclasses import dataclass, field

from randomizer.options import (
    DEFAULT_OPTIONS,
    MAX_XP_RATE_PERCENT,
    MIN_XP_RATE_PERCENT,
    XP_RATE_STEP,
    RandomizerOptions,
)


class LegacyFlagsError(ValueError):
    pass


@dataclass
class LegacyFlagsResult:
    options: RandomizerOptions
    style: str
    warnings: list[str] = field(default_factory=list)


def _round_xp_rate(value: float, warnings: list[str]) -> int:
    rounded = round(value / XP_RATE_STEP) * XP_RATE_STEP
    clamped = max(MIN_XP_RATE_PERCENT, min(MAX_XP_RATE_PERCENT, rounded))
    if clamped != value:
        warnings.append(f"Legacy XP value {value:g} was rounded to {clamped}%.")
    return clamped


def parse_legacy_flags(flag_string: str) -> LegacyFlagsResult:
    """Best-effort conversion of the old compact and web flag strings.

    The old format was ambiguous between the desktop encoder and the web
    encoder (notably for bosses and XP scaling). We detect the web style by its
    multi-character tokens and otherwise treat the value as the compact desktop
    style. The result is always the new canonical options.
    """
    flags = (flag_string or "").strip()
    if not flags:
        raise LegacyFlagsError("The old link does not contain any flags. Please remake the link.")

    web_markers = ("Op", "Sv", "Tv", "Gv", "Xp")
    if any(marker in flags for marker in web_markers):
        return _parse_web_flags(flags)
    return _parse_compact_flags(flags)


def _parse_web_flags(flags: str) -> LegacyFlagsResult:
    warnings = ["Old web link converted to the new flag format."]
    xp_match = re.search(r"Xp(\d+)", flags)
    if xp_match:
        xp_rate = _round_xp_rate(int(xp_match.group(1)) * 10, warnings)
    else:
        xp_rate = DEFAULT_OPTIONS.xp_rate_percent

    options = RandomizerOptions(
        shuffle_key_items="Op" not in flags,
        randomize_shops="Sv" not in flags,
        randomize_treasure="Tv" not in flags,
        randomize_starting_gear="Gv" not in flags,
        randomize_bosses="B" not in flags,
        new_item_distribution="Ni" in flags,
        fiend_ribbons="R" in flags,
        xp_rate_percent=xp_rate,
    )
    return LegacyFlagsResult(options=options, style="web", warnings=warnings)


def _parse_compact_flags(flags: str) -> LegacyFlagsResult:
    warnings = ["Old compact link converted to the new flag format. XP values are approximate."]

    digits_match = re.search(r"(\d+)$", flags)
    if digits_match:
        digits = int(digits_match.group(1))
        letters = flags[:digits_match.start()]
        if digits <= 0:
            raise LegacyFlagsError("Invalid legacy XP value.")
        # The old encoder wrote int(scale_levels * 10), where scale_levels is
        # the XP requirement multiplier. Convert that to a level-up speed.
        xp_rate = _round_xp_rate(1000 / digits, warnings)
    else:
        letters = flags
        xp_rate = DEFAULT_OPTIONS.xp_rate_percent
        warnings.append("No legacy XP value found; using the default XP speed.")

    tokens = {
        "K": "shuffle_key_items",
        "S": "randomize_shops",
        "T": "randomize_treasure",
        "G": "randomize_starting_gear",
        "B": "randomize_bosses",
        "R": "fiend_ribbons",
    }
    values = {
        "shuffle_key_items": False,
        "randomize_shops": False,
        "randomize_treasure": False,
        "randomize_starting_gear": False,
        "randomize_bosses": False,
        "new_item_distribution": False,
        "fiend_ribbons": False,
        "xp_rate_percent": xp_rate,
    }

    index = 0
    while index < len(letters):
        if letters.startswith("Ni", index):
            values["new_item_distribution"] = True
            index += 2
        elif letters[index] in tokens:
            values[tokens[letters[index]]] = True
            index += 1
        elif letters.startswith("\\u819a", index):
            # The old debug marker. Keep it out of public links.
            index += len("\\u819a")
            warnings.append("Legacy debug marker ignored.")
        else:
            warnings.append(f"Ignored unknown legacy flag '{letters[index]}'.")
            index += 1

    try:
        options = RandomizerOptions(**values)
    except (TypeError, ValueError) as exc:
        raise LegacyFlagsError(str(exc)) from exc
    return LegacyFlagsResult(options=options, style="compact", warnings=warnings)
