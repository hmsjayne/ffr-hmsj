#  Copyright 2019 Nicole Borrelli
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

from doslib.rom import Rom
from stream.input import Input
from stream.output import Output


class TextBlock(object):
    def __init__(self, rom: Rom, lut_offset: int, count: int):
        self.lut_offset = lut_offset
        self.lut = list(rom.get_lut(lut_offset, count))
        self.strings = []
        for addr in self.lut:
            self.strings.append(rom.get_string(Rom.pointer_to_offset(addr)))

    def __getitem__(self, index):
        return TextBlock._as_ascii(Input(self.strings[index], check_alignment=False))

    def __setitem__(self, index, value):
        self.strings[index] = TextBlock._encode_text(Input(value, check_alignment=False))

    def size(self):
        return len(self.strings)

    def pack(self, rom: Rom) -> Rom:
        text_block = Output()
        text_lut = Output()

        next_addr = self.lut[0]
        text_block_offset = Rom.pointer_to_offset(next_addr)

        for index, data in enumerate(self.strings):
            if data is not None:
                text_lut.put_u32(next_addr)
                text_block.put_bytes(data)
                next_addr += len(data)
            else:
                text_lut.put_u32(self.lut[0])

        patches = {
            self.lut_offset: text_lut.get_buffer(),
            text_block_offset: text_block.get_buffer()
        }
        return rom.apply_patches(patches)

    @staticmethod
    def encode_text(text: str):
        data = bytearray()
        for char in text:
            data.append(ord(char))
        return TextBlock._encode_text(Input(data))

    @staticmethod
    def _as_ascii(stream: Input, symbolic_names: bool = False):
        working = ""
        while not stream.is_eos():
            char_code = stream.get_u8()
            if char_code > 0x80:
                char_code = (char_code << 8) | stream.get_u8()
            elif char_code == 0x25:
                char_code = (char_code << 8) | stream.get_u8()
                next_char = stream.get_u8()

                if char_code == 0x2532 and next_char == 0x64:
                    char_code = 0x253264
                else:
                    stream.unget_u8()
            elif char_code in TextBlock.TEXT_TABLE:
                char_code = char_code
            else:
                print(f"Unknown code encountered in string: {hex(char_code)}")

            to_append = TextBlock.TEXT_TABLE[char_code] if char_code in TextBlock.TEXT_TABLE else None
            if not symbolic_names:
                if to_append is None or (len(to_append) > 1 and not to_append.startswith("\\")):
                    working += TextBlock._escape(char_code)
                else:
                    working += to_append
            else:
                if to_append is not None:
                    working += to_append
                else:
                    working += TextBlock._escape(char_code)

        return working

    @staticmethod
    def _encode_text(stream):
        working = bytearray()
        while not stream.is_eos():
            char = stream.get_char()
            if char == '\\':
                char = stream.get_char()
                if char == 'x':
                    # \x designates a 2 digit hex code
                    chars = (stream.get_u8() << 8) + stream.get_u8()
                elif char == 'u':
                    # \u designates a 4 digit hex code
                    num = ""
                    for digit in range(4):
                        num += hex(stream.get_u8())
                    chars = int(num, 16)
                elif char == '\"':
                    chars = 0x815F
                elif char == 'n':
                    chars = 0xa
                else:
                    raise RuntimeError(f"Invalid escape character: {char}")
            else:
                chars = TextBlock.INVERTED_TEXT_TABLE[char]

            digits = int(len(hex(chars)) / 2) - 1
            working += int(chars).to_bytes(digits, byteorder="big", signed=False)

        working.append(0x0)
        return working

    @staticmethod
    def _escape(char_code: int):
        if char_code <= 0xff:
            escaped = f"\\x{char_code:02x}"
        elif char_code <= 0xffff:
            escaped = f"\\u{char_code:04x}"
        else:
            escaped = f"\\U{char_code:08x}"
        return escaped

    TEXT_TABLE = {
        0x00: "(End)",
        0x0A: "\\n",
        0x2D: "(Dash)",
        0x2E: "(period)",
        0x30: "(%1)",
        0x2530: "(E_Item)",
        0x2531: "(E_Price)",
        0x2532: "(E_Char)",
        0x2573: "(E_Type)",
        0x2564: "(E_Amount)",
        0x253264: "[E_Beaver)",
        0x810A: "(cr)",
        0x8140: " ",
        0x8143: ",",
        0x8144: ".",
        0x8145: "?",
        0x8146: ":",
        0x8147: ";",
        0x8148: "?",
        0x8149: "!",
        0x8151: "_",
        0x815E: "/",
        0x815F: "\"",
        0x8160: "~",
        0x8163: "(...)",
        0x8164: "(..)",
        0x8165: "(' )",
        0x8166: "( ')",
        0x8167: "(\" )",
        0x8168: "( \")",
        0x8169: "(",
        0x816A: ")",
        0x816D: "[",
        0x816E: "]",
        0x816F: "{",
        0x8170: "}",
        0x8173: "«",
        0x8174: "»",
        0x817B: "+",
        0x817C: "-",
        0x8193: "%",
        0x8195: "&",
        0x8196: "*",
        0x8197: "@",
        0x819A: "(Star)",
        0x819B: "(Circle)",
        0x81A3: "(upTriangle)",
        0x81A5: "(downTriangle)",
        0x81A8: "(rightArrow)",
        0x81A9: "(leftArrow)",
        0x81AA: "(upArrow)",
        0x81AB: "(downArrow)",
        0x824F: "0",
        0x8250: "1",
        0x8251: "2",
        0x8252: "3",
        0x8253: "4",
        0x8254: "5",
        0x8255: "6",
        0x8256: "7",
        0x8257: "8",
        0x8258: "9",
        0x8260: "A",
        0x8261: "B",
        0x8262: "C",
        0x8263: "D",
        0x8264: "E",
        0x8265: "F",
        0x8266: "G",
        0x8267: "H",
        0x8268: "I",
        0x8269: "J",
        0x826A: "K",
        0x826B: "L",
        0x826C: "M",
        0x826D: "N",
        0x826E: "O",
        0x826F: "P",
        0x8270: "Q",
        0x8271: "R",
        0x8272: "S",
        0x8273: "T",
        0x8274: "U",
        0x8275: "V",
        0x8276: "W",
        0x8277: "X",
        0x8278: "Y",
        0x8279: "Z",
        0x8281: "a",
        0x8282: "b",
        0x8283: "c",
        0x8284: "d",
        0x8285: "e",
        0x8286: "f",
        0x8287: "g",
        0x8288: "h",
        0x8289: "i",
        0x828A: "j",
        0x828B: "k",
        0x828C: "l",
        0x828D: "m",
        0x828E: "n",
        0x828F: "o",
        0x8290: "p",
        0x8291: "q",
        0x8292: "r",
        0x8293: "s",
        0x8294: "t",
        0x8295: "u",
        0x8296: "v",
        0x8297: "w",
        0x8298: "x",
        0x8299: "y",
        0x829A: "z",
        0x829F: "Œ",
        0x82A0: "œ",
        0x82A1: "¡",
        0x82A2: "¿",
        0x82A3: "À",
        0x82A4: "Á",
        0x82A5: "Â",
        0x82A6: "Ä",
        0x82A7: "Ç",
        0x82A8: "È",
        0x82A9: "É",
        0x82AA: "Ê",
        0x82AB: "Ë",
        0x82AC: "Ì",
        0x82AD: "Í",
        0x82AE: "Î",
        0x82AF: "Ï",
        0x82B0: "Ñ",
        0x82B1: "Ò",
        0x82B2: "Ó",
        0x82B3: "Ô",
        0x82B4: "Ö",
        0x82B5: "Ù",
        0x82B6: "Ú",
        0x82B7: "Û",
        0x82B8: "Ü",
        0x82B9: "ß",
        0x82BA: "à",
        0x82BB: "á",
        0x82BC: "â",
        0x82BD: "ä",
        0x82BE: "ç",
        0x82BF: "è",
        0x82C0: "é",
        0x82C1: "ê",
        0x82C2: "ë",
        0x82C3: "ì",
        0x82C4: "í",
        0x82C5: "î",
        0x82C6: "ï",
        0x82C7: "ñ",
        0x82C8: "ò",
        0x82C9: "ó",
        0x82CA: "ô",
        0x82CB: "ö",
        0x82CC: "ù",
        0x82CD: "ú",
        0x82CE: "û",
        0x82CF: "ü",
        0x82D0: "(Heart)",
        0x82D1: "„",
        0x8300: "(Treasure2)",
        0x8301: "(Potion2)",
        0x8302: "(Tent2)",
        0x8303: "(Item2)",
        0x8304: "(Shield2)",
        0x8305: "(Knife2)",
        0x8306: "(Rapier2)",
        0x8307: "(Staff2)",
        0x8308: "(Mace)",
        0x8309: "(Spear)",
        0x830A: "(Sword2)",
        0x830B: "(Katana)",
        0x830C: "(Axe2)",
        0x830D: "(DoubleAxe)",
        0x830E: "(Bow)",
        0x830F: "(Helmet2)",
        0x8310: "(Robe)",
        0x8311: "(Armor2)",
        0x8312: "(Gloves2)",
        0x8313: "(Book)",
        0x8314: "(Trash2)",
        0x8315: "(Fist)",
        0x8316: "(White Magic2)",
        0x8317: "(Black Magic2)",
        0x8740: "(Sword)",
        0x8741: "(Katana)",
        0x8742: "(Knife)",
        0x8743: "(Nunchaku)",
        0x8744: "(Axe)",
        0x8745: "(Hammer)",
        0x8746: "(Staff)",
        0x8747: "(Shirt)",
        0x8748: "(Armor)",
        0x8749: "(Armlet)",
        0x874A: "(Shield)",
        0x874B: "(Helmet)",
        0x874C: "(Gloves)",
        0x874D: "(White Magic)",
        0x874E: "(Black Magic)",
        0x874F: "(Potion)",
        0x8750: "(Item)",
        0x8751: "(Tent)",
        0x8752: "(Chest)",
        0x8753: "(Trash)",
        0x8754: "(??)"
    }
    INVERTED_TEXT_TABLE = dict([[v, k] for k, v in TEXT_TABLE.items()])
