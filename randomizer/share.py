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
from urllib.parse import parse_qs, urlencode

from randomizer.legacy_flags import LegacyFlagsError, parse_legacy_flags
from randomizer.options import ALGORITHM_VERSION, DEFAULT_OPTIONS, RandomizerOptions
from randomizer.seed import normalize_seed

OPTION_PARAMS = {
    "shuffle_key_items": "keys",
    "randomize_shops": "shops",
    "randomize_treasure": "treasure",
    "randomize_starting_gear": "gear",
    "randomize_bosses": "bosses",
    "new_item_distribution": "items",
    "fiend_ribbons": "ribbons",
    "xp_rate_percent": "xp",
}
PARAM_TO_OPTION = {value: key for key, value in OPTION_PARAMS.items()}
SUPPORTED_LINK_VERSIONS = {2, ALGORITHM_VERSION}

TRUE_VALUES = {"1", "true", "yes", "on"}
FALSE_VALUES = {"0", "false", "no", "off"}


class ShareLinkError(ValueError):
    pass


@dataclass
class ShareLink:
    seed: str
    options: RandomizerOptions
    warnings: list[str] = field(default_factory=list)
    legacy: bool = False
    rewritten_fragment: str | None = None


def _format_value(name: str, value) -> str:
    if name == "xp_rate_percent":
        return str(value)
    return "1" if value else "0"


def encode_share_fragment(seed: str, options: RandomizerOptions | None = None) -> str:
    """Encode a shareable URL fragment, including only non-default options."""
    seed = normalize_seed(seed)
    options = options or DEFAULT_OPTIONS
    params = [
        ("v", str(ALGORITHM_VERSION)),
        ("seed", seed),
    ]
    defaults = DEFAULT_OPTIONS.public_dict()
    for name, param_name in OPTION_PARAMS.items():
        value = getattr(options, name)
        if value != defaults[name]:
            params.append((param_name, _format_value(name, value)))
    return "#" + urlencode(params)


def _fragment_payload(fragment: str) -> str:
    if "#" in fragment:
        fragment = fragment.split("#", 1)[1]
    elif fragment.startswith("?"):
        fragment = fragment[1:]
    return fragment


def _parse_bool(param: str, value: str, warnings: list[str]) -> bool:
    normalized = value.strip().lower()
    if normalized in TRUE_VALUES:
        return True
    if normalized in FALSE_VALUES:
        return False
    raise ShareLinkError(f"Invalid boolean value for '{param}': {value!r}")


def parse_share_fragment(fragment: str) -> ShareLink:
    raw = _fragment_payload(fragment)
    params = parse_qs(raw, keep_blank_values=True)

    if "flags" in params and "v" not in params:
        if "seed" not in params:
            raise ShareLinkError("Legacy link is missing a seed.")
        seed = normalize_seed(params["seed"][0])
        try:
            legacy = parse_legacy_flags(params["flags"][0])
        except LegacyFlagsError as exc:
            raise ShareLinkError(str(exc)) from exc
        return ShareLink(
            seed=seed,
            options=legacy.options,
            warnings=legacy.warnings,
            legacy=True,
            rewritten_fragment=encode_share_fragment(seed, legacy.options),
        )

    if "v" not in params:
        raise ShareLinkError("Unsupported link format; please remake the link.")
    try:
        link_version = int(params["v"][0])
    except ValueError as exc:
        raise ShareLinkError(f"Invalid link version: {params['v'][0]!r}") from exc
    if link_version not in SUPPORTED_LINK_VERSIONS:
        raise ShareLinkError(
            f"Unsupported link version {link_version}; expected {ALGORITHM_VERSION}."
        )
    if "seed" not in params:
        raise ShareLinkError("Link is missing a seed.")
    seed = normalize_seed(params["seed"][0])

    values = DEFAULT_OPTIONS.public_dict()
    warnings = []
    upgrade_link = link_version < ALGORITHM_VERSION
    if upgrade_link:
        warnings.append(
            f"Link uses algorithm v{link_version}; it will run with v{ALGORITHM_VERSION}."
        )
    for param, raw_values in params.items():
        if param in ("v", "seed"):
            continue
        if param not in PARAM_TO_OPTION:
            warnings.append(f"Ignored unknown link option '{param}'.")
            continue
        name = PARAM_TO_OPTION[param]
        raw_value = raw_values[-1]
        if name == "xp_rate_percent":
            try:
                values[name] = int(raw_value)
            except ValueError as exc:
                raise ShareLinkError(f"Invalid XP value: {raw_value!r}") from exc
        else:
            values[name] = _parse_bool(param, raw_value, warnings)

    try:
        options = RandomizerOptions(**values)
    except (TypeError, ValueError) as exc:
        raise ShareLinkError(str(exc)) from exc
    return ShareLink(
        seed=seed,
        options=options,
        warnings=warnings,
        legacy=upgrade_link,
        rewritten_fragment=encode_share_fragment(seed, options) if upgrade_link else None,
    )


def build_filename(seed: str, options: RandomizerOptions,
                   base_name: str = "ff1-dos", extension: str = "gba") -> str:
    seed = normalize_seed(seed)
    slug = re.sub(r"[^A-Za-z0-9_-]+", "-", seed).strip("-") or "seed"
    return f"{base_name}_v{ALGORITHM_VERSION}_{options.short_code()}_{slug}.{extension}"
