#!/usr/bin/env python3

import sys

from ffa.rom import open_rom, load_monster_data


def main(argv):
  rom = open_rom(argv[0])
  
  monsters = load_monster_data(rom)

if __name__ == "__main__":
  main(sys.argv[1:])
