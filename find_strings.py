#!/usr/bin/env python3
import argparse
import sys
from typing import Optional

from doslib.rom import Rom
import array

# --- Encoding Map ---
# Based on the table provided by the user.
# Keys are 'bytes' objects, values are the decoded string representation.
DECODING_MAP = {
    # Single-byte characters
    b'\x0a': '\n',  # (Newline) - Converted to a real newline for readability
    b'\x2d': '-',  # (Dash)
    b'\x2e': '.',  # (period)

    # Two-byte characters
    b'\x81\x0a': '(cr)',
    b'\x81\x40': ' ',
    b'\x81\x43': ',',
    b'\x81\x44': '.',
    b'\x81\x45': '?',
    b'\x81\x46': ':',
    b'\x81\x47': ';',
    b'\x81\x48': '?',
    b'\x81\x49': '!',
    b'\x81\x51': '_',
    b'\x81\x5e': '/',
    b'\x81\x5f': '\\',
    b'\x81\x60': '~',
    b'\x81\x63': '...',
    b'\x81\x64': '..',
    b'\x81\x65': "' ",
    b'\x81\x66': " '",
    b'\x81\x67': '" ',
    b'\x81\x68': ' "',
    b'\x81\x69': '(',
    b'\x81\x6a': ')',
    b'\x81\x6d': '[',
    b'\x81\x6e': ']',
    b'\x81\x6f': '{',
    b'\x81\x70': '}',
    b'\x81\x73': '«',
    b'\x81\x74': '»',
    b'\x81\x7b': '+',
    b'\x81\x7c': '-',
    b'\x81\x93': '%',
    b'\x81\x95': '&',
    b'\x81\x96': '*',
    b'\x81\x97': '@',
    b'\x81\x9a': '(Star)',
    b'\x81\x9b': '(Circle)',
    b'\x81\xa3': '(upTriangle)',
    b'\x81\xa5': '(downTriangle)',
    b'\x81\xa8': '(rightArrow)',
    b'\x81\xa9': '(leftArrow)',
    b'\x81\xaa': '(upArrow)',
    b'\x81\xab': '(downArrow)',
    b'\x82\x4f': '0',
    b'\x82\x50': '1',
    b'\x82\x51': '2',
    b'\x82\x52': '3',
    b'\x82\x53': '4',
    b'\x82\x54': '5',
    b'\x82\x55': '6',
    b'\x82\x56': '7',
    b'\x82\x57': '8',
    b'\x82\x58': '9',
    b'\x82\x60': 'A',
    b'\x82\x61': 'B',
    b'\x82\x62': 'C',
    b'\x82\x63': 'D',
    b'\x82\x64': 'E',
    b'\x82\x65': 'F',
    b'\x82\x66': 'G',
    b'\x82\x67': 'H',
    b'\x82\x68': 'I',
    b'\x82\x69': 'J',
    b'\x82\x6a': 'K',
    b'\x82\x6b': 'L',
    b'\x82\x6c': 'M',
    b'\x82\x6d': 'N',
    b'\x82\x6e': 'O',
    b'\x82\x6f': 'P',
    b'\x82\x70': 'Q',
    b'\x82\x71': 'R',
    b'\x82\x72': 'S',
    b'\x82\x73': 'T',
    b'\x82\x74': 'U',
    b'\x82\x75': 'V',
    b'\x82\x76': 'W',
    b'\x82\x77': 'X',
    b'\x82\x78': 'Y',
    b'\x82\x79': 'Z',
    b'\x82\x81': 'a',
    b'\x82\x82': 'b',
    b'\x82\x83': 'c',
    b'\x82\x84': 'd',
    b'\x82\x85': 'e',
    b'\x82\x86': 'f',
    b'\x82\x87': 'g',
    b'\x82\x88': 'h',
    b'\x82\x89': 'i',
    b'\x82\x8a': 'j',
    b'\x82\x8b': 'k',
    b'\x82\x8c': 'l',
    b'\x82\x8d': 'm',
    b'\x82\x8e': 'n',
    b'\x82\x8f': 'o',
    b'\x82\x90': 'p',
    b'\x82\x91': 'q',
    b'\x82\x92': 'r',
    b'\x82\x93': 's',
    b'\x82\x94': 't',
    b'\x82\x95': 'u',
    b'\x82\x96': 'v',
    b'\x82\x97': 'w',
    b'\x82\x98': 'x',
    b'\x82\x99': 'y',
    b'\x82\x9a': 'z',
    b'\x82\x9f': 'Œ',
    b'\x82\xa0': 'œ',
    b'\x82\xa1': '¡',
    b'\x82\xa2': '¿',
    b'\x82\xa3': 'À',
    b'\x82\xa4': 'Á',
    b'\x82\xa5': 'Â',
    b'\x82\xa6': 'Ä',
    b'\x82\xa7': 'Ç',
    b'\x82\xa8': 'È',
    b'\x82\xa9': 'É',
    b'\x82\xaa': 'Ê',
    b'\x82\xab': 'Ë',
    b'\x82\xac': 'Ì',
    b'\x82\xad': 'Í',
    b'\x82\xae': 'Î',
    b'\x82\xaf': 'Ï',
    b'\x82\xb0': 'Ñ',
    b'\x82\xb1': 'Ò',
    b'\x82\xb2': 'Ó',
    b'\x82\xb3': 'Ô',
    b'\x82\xb4': 'Ö',
    b'\x82\xb5': 'Ù',
    b'\x82\xb6': 'Ú',
    b'\x82\xb7': 'Û',
    b'\x82\xb8': 'Ü',
    b'\x82\xb9': 'ß',
    b'\x82\xba': 'à',
    b'\x82\xbb': 'á',
    b'\x82\xbc': 'â',
    b'\x82\xbd': 'ä',
    b'\x82\xbe': 'ç',
    b'\x82\xbf': 'è',
    b'\x82\xc0': 'é',
    b'\x82\xc1': 'ê',
    b'\x82\xc2': 'ë',
    b'\x82\xc3': 'ì',
    b'\x82\xc4': 'í',
    b'\x82\xc5': 'î',
    b'\x82\xc6': 'ï',
    b'\x82\xc7': 'ñ',
    b'\x82\xc8': 'ò',
    b'\x82\xc9': 'ó',
    b'\x82\xca': 'ô',
    b'\x82\xcb': 'ö',
    b'\x82\xcc': 'ù',
    b'\x82\xcd': 'ú',
    b'\x82\xce': 'û',
    b'\x82\xcf': 'ü',
    b'\x82\xd0': '(Heart)',
    b'\x82\xd1': '„',
    b'\x83\x00': '(Treasure2)',
    b'\x83\x01': '(Potion2)',
    b'\x83\x02': '(Tent2)',
    b'\x83\x03': '(Item2)',
    b'\x83\x04': '(Shield2)',
    b'\x83\x05': '(Knife2)',
    b'\x83\x06': '(Rapier2)',
    b'\x83\x07': '(Staff2)',
    b'\x83\x08': '(Mace)',
    b'\x83\x09': '(Spear)',
    b'\x83\x0a': '(Sword2)',
    b'\x83\x0b': '(Katana)',
    b'\x83\x0c': '(Axe2)',
    b'\x83\x0d': '(DoubleAxe)',
    b'\x83\x0e': '(Bow)',
    b'\x83\x0f': '(Helmet2)',
    b'\x83\x10': '(Robe)',
    b'\x83\x11': '(Armor2)',
    b'\x83\x12': '(Gloves2)',
    b'\x83\x13': '(Book)',
    b'\x83\x14': '(Trash2)',
    b'\x83\x15': '(Fist)',
    b'\x83\x16': '(White Magic2)',
    b'\x83\x17': '(Black Magic2)',
    b'\x87\x40': '(Sword)',
    b'\x87\x41': '(Katana)',

    b'\x87\x42': '(Knife)',
    b'\x87\x43': '(Nunchaku)',
    b'\x87\x44': '(Axe)',
    b'\x87\x45': '(Hammer)',
    b'\x87\x46': '(Staff)',
    b'\x87\x47': '(Shirt)',
    b'\x87\x48': '(Armor)',
    b'\x87\x49': '(Armlet)',
    b'\x87\x4a': '(Shield)',
    b'\x87\x4b': '(Helmet)',
    b'\x87\x4c': '(Gloves)',
    b'\x87\x4d': '(White Magic)',
    b'\x87\x4e': '(Black Magic)',
    b'\x87\x4f': '(Potion)',
    b'\x87\x50': '(Item)',
    b'\x87\x51': '(Tent)',
    b'\x87\x52': '(Chest)',
    b'\x87\x53': '(Trash)',
    b'\x87\x54': '(??)',
}

TERMINATOR = b'\x00'


def decode_string_from_offset(data, offset, max_unknown):
    """
    Attempts to decode a string starting at a given offset, allowing for
    a specified number of unknown 2-byte characters.

    Args:
        data (bytes): The binary data of the file.
        offset (int): The starting position to attempt decoding from.
        max_unknown (int): The maximum number of unknown 2-byte sequences allowed.

    Returns:
        A tuple (decoded_string, length_of_encoded_string_in_bytes).
        Returns (None, 0) if a valid string cannot be decoded from the offset.
    """
    decoded_chars = []
    pos = offset
    unknown_count = 0

    while pos < len(data):
        # Check for terminator first
        if data[pos:pos + 1] == TERMINATOR:
            return "".join(decoded_chars), (pos - offset) + 1

        # Check for two-byte character (ensure we don't read past the end of the file)
        if pos + 1 < len(data):
            two_byte_char = data[pos:pos + 2]
            two_byte_char = bytes(two_byte_char)
            if two_byte_char in DECODING_MAP:
                decoded_chars.append(DECODING_MAP[two_byte_char])
                pos += 2
                continue

        # Check for one-byte character
        one_byte_char = data[pos:pos + 1]
        one_byte_char = bytes(one_byte_char)
        if one_byte_char in DECODING_MAP:
            decoded_chars.append(DECODING_MAP[one_byte_char])
            pos += 1
            continue

        # --- Handle unknown characters ---
        # An unknown was found. Check if we can tolerate it.

        # Rule: Unknowns cannot be the first character of a string.
        if pos == offset:
            return None, 0

        # Rule: We must have enough bytes left for a 2-byte sequence.
        if pos + 1 >= len(data):
            return None, 0  # Not enough data for our assumed 2-byte unknown

        # Rule: Check if we have exceeded the maximum allowed unknowns.
        unknown_count += 1
        if unknown_count > max_unknown:
            return None, 0

        # If we're here, we tolerate this unknown. Record it and continue.
        unknown_bytes = data[pos:pos + 2]
        placeholder = f'[{unknown_bytes.hex().upper()}]'
        decoded_chars.append(placeholder)
        pos += 2

    # If the loop finishes without finding a terminator, it's not a valid null-terminated string.
    return None, 0


def find_and_decode_strings(data:bytearray, ptrs:dict[int,list[int]], min_len=3, max_unknown=0):
    """
    Scans the binary data to find and decode all possible strings.

    Args:
        data (bytes): The binary data of the file.
        min_len (int): The minimum length of a decoded string to be printed.
        max_unknown (int): Max number of unknown 2-byte sequences to allow.
    """
    i = 0
    file_len = len(data)
    found_count = 0

    while i < file_len:
        # Try to decode a string starting at the current offset `i`
        decoded_str, encoded_len = decode_string_from_offset(
            data, i, max_unknown)

        if decoded_str is not None and len(decoded_str) >= min_len:
            print(f"{hex(i)}: {decoded_str.replace(chr(10), r'\\n')}")
            str_addr = Rom.offset_to_pointer(i)
            if str_addr in ptrs:
                for p in ptrs[str_addr]:
                    print(f" - {hex(p)}")

            found_count += 1
            i += encoded_len
        else:
            i += 1

    if found_count == 0:
        print("No strings found with the specified encoding and parameters.")

def find_ptrs(rom: Rom) -> dict[int, list[int]]:
    offset = 0
    rom_size = len(rom.rom_data)
    top_addr = rom.offset_to_pointer(rom_size)

    pointers:dict[int, list[int]] = {}

    for offset in range(0, rom_size, 4):
        value = array.array("I", rom.rom_data[offset:offset + 4])[0]

        check_ptr = False
        if 0x08000000 < value < top_addr:
            # Valid address, maybe a pointer
            pass
        else:
            continue

        if value not in pointers:
            pointers[value] = list()
        pointers[value].append(offset)
    return pointers

def main():
    """
    Main function to parse arguments and run the decoder.
    """
    parser = argparse.ArgumentParser(
        description="Find and decode null-terminated strings from a binary file using a custom encoding.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("filepath", help="Path to the binary file to scan.")
    parser.add_argument(
        "--min-len",
        type=int,
        default=3,
        help="Minimum length of decoded strings to display (default: 3)."
    )
    parser.add_argument(
        "--max-unknown",
        type=int,
        default=0,
        help="Maximum number of unknown 2-byte sequences to allow in a string (default: 3)."
    )
    args = parser.parse_args()

    rom:Rom

    try:
        with open(args.filepath, "rb") as rom_file:
            rom_data = bytearray(rom_file.read())
            rom_file.close()
            rom = Rom(rom_data)
    except FileNotFoundError:
        print(f"Error: The file '{args.filepath}' was not found.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"An error occurred while reading the file: {e}", file=sys.stderr)
        sys.exit(1)

    pointers = find_ptrs(rom)
    find_and_decode_strings(rom.rom_data, pointers, args.min_len, args.max_unknown)


if __name__ == "__main__":
    main()
