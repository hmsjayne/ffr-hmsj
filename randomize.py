#!/usr/bin/env python3

import sys

from ffa.rom import open_rom, write_rom
from ipsfile import apply_patches, load_ips_files

BASE_PATCHES = [
    "data/DataPointerConsolidation.ips",
    "data/FF1EncounterToggle.ips",
    "data/ImprovedEquipmentStatViewing.ips",
    "data/NoEscape.ips",
    "data/RandomDefault.ips",
    "data/RunningChange.ips",
    "data/StatusScreenExpansion.ips",
]


def main(argv):
    rom = open_rom(argv[0])

    airship_patch = load_ips_files(*BASE_PATCHES)
    rom = apply_patches(rom, airship_patch)
    write_rom("ffr-dos.gba", rom)


if __name__ == "__main__":
    main(sys.argv[1:])
