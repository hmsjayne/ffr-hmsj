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

from event.tokens import *

# The grammar for `easm` is very simple, and is defined in the dict here.


GRAMMAR = {
    # Here we define mappings of strings to terminal tokens.
    # If a string is not defined here, it will likely cause a SyntaxError exception.
    "end_event": EndEventToken,
    "load_text": LoadTextToken,
    "close_dialog": CloseDialogToken,
    "jump": JumpToken,
    "music": MusicToken,
    "show_dialog": ShowDialogToken,
    "set_flag": SetFlagToken,
    "check_flag": CheckFlagToken,
    "remove_trigger": RemoveTriggerToken,
    "npc_update": NpcUpdateToken,
    "give_item": GiveItemToken,
    "take_item": TakeItemToken,
    "check_item": CheckItemToken,

    # Conditional jumps
    "jz": JzToken,
    "jnz": JnzToken,

    # Here are various other keywords that are command specific.
    "top": LoadTextTopToken,
    "bot": LoadTextBottomToken,
    "wait": CloseDialogWaitToken,
    "auto": CloseDialogAutoToken,

    #
    # Define various non-terminal tokens here.
    #
    "value": (SymbolToken, NumberToken),
    "cond": (JzToken, JnzToken),

    #
    # Define the structure of each command here.
    # Commands that don't match the patterns here will raise a SyntaxError exception.
    #
    EndEventToken: None,
    LoadTextToken: [(LoadTextTopToken, LoadTextBottomToken)],
    CloseDialogToken: [(CloseDialogAutoToken, CloseDialogWaitToken)],
    JumpToken: [LabelToken],
    MusicToken: ["value", "value"],
    ShowDialogToken: None,
    SetFlagToken: ["value"],
    CheckFlagToken: ["value", "cond", LabelToken],
    RemoveTriggerToken: ["value"],
    NpcUpdateToken: ["value", "value"],
    GiveItemToken: ["value"],
    TakeItemToken: ["value"],
    CheckItemToken: ["value", JzToken, LabelToken],

    # One command is missing a definition here: db
    # This command is handled separately by the parser, because it is essentially a request to insert the
    # bytes that proceed it verbatim into the output. Because the command can be followed by any number
    # of bytes, it's easiest to just not try to worry about coding that into the grammar.
    "db": RawCommandToken
}


class Uint16(object):
    def __init__(self, value: int):
        self._value = value

    def __repr__(self):
        return f"Unit16({hex(self._value)})"

    def bytes(self):
        return [self._value & 0xff, (self._value >> 8) & 0xff]


class Uint32(object):
    def __init__(self, value: int):
        self._value = value

    def __repr__(self):
        return f"Uint32({hex(self._value)})"

    def bytes(self):
        return [self._value & 0xff, (self._value >> 8) & 0xff, (self._value >> 16) & 0xff, (self._value >> 24) & 0xff]


class InputString(object):
    def __init__(self, data: str):
        self._data = data
        self._index = 0

    def getc(self):
        char = self.peek()
        if char is not None:
            self._index += 1
        return char

    def ungetc(self):
        if self._index > 0:
            self._index -= 1

    def peek(self):
        if self._index < len(self._data):
            return self._data[self._index]
        else:
            return None

    def get_int(self) -> int:
        working = ""
        is_hex = False

        char = self.getc()
        while char is not None and (char.isdigit() or (is_hex and char.lower() in ['a', 'b', 'c', 'd', 'e', 'f'])):
            working += char

            char = self.getc()

            # Special case for hex number
            if len(working) == 1 and (char == 'x' or char == 'X'):
                is_hex = True
                working += char
                char = self.getc()

        if is_hex:
            return int(working, 16)
        else:
            return int(working)


class ParserSyntaxError(RuntimeError):
    def __init__(self, token, line, line_number):
        super().__init__(f"Unexpected token '{token}' on line {line_number}: {line}")


class TokenStream(object):
    def __init__(self, line: str, line_number: int):
        self._tokens = self._tokenize(line)
        self._index = 0

        self._input_line = line
        self._line_number = line_number

    def peek(self):
        if self._index < len(self._tokens):
            return self._tokens[self._index]
        else:
            return None

    def next(self):
        token = self.peek()
        if token is not None:
            self._index += 1
        return token

    def expect(self, *token_types):
        token = self.next()
        if token not in token_types:
            raise ParserSyntaxError(token, self._input_line, self._line_number)
        return token

    def _get_alphanum_token(self, working: InputString) -> str:
        # Identifiers are alphanumeric, but start with a letter. They may include '_' because ... Python?
        current = ""
        char = working.getc()
        while char is not None and (char.isalnum() or char == '_'):
            current += char
            char = working.getc()

        # Took one too many characters, potentially.
        if char is not None:
            working.ungetc()

        # Return what we got
        return current

    def _tokenize(self, line: str) -> list:
        tokens = []

        current = InputString(line)
        char = current.getc()
        while char is not None:
            if char.isspace():
                # Ignore whitespace...
                pass
            elif char.isalpha():
                current.ungetc()
                tokens.append(KeywordToken(self._get_alphanum_token(current)))
            elif char.isdigit():
                # Numbers are all ints and just parsed by the stream - makes this easier
                current.ungetc()
                tokens.append(NumberToken(current.get_int()))
            elif char == '.':
                if current.peek().isalpha():
                    tokens.append(LabelToken(self._get_alphanum_token(current)))
                else:
                    raise RuntimeError(f"Illegal label definition, starts with: {current.peek()}")
            elif char == '%':
                if current.peek().isalpha():
                    tokens.append(SymbolToken(self._get_alphanum_token(current)))
                else:
                    raise RuntimeError(f"Illegal label definition, starts with: {current.peek()}")
            elif char == ':':
                tokens.append(ColonToken(":"))
            elif char == ";":
                comment = ";"
                while current.peek() is not None:
                    comment += current.getc()
                tokens.append(CommentToken(comment))
            else:
                # Symbols are single characters
                tokens.append(char)

            char = current.getc()

        return tokens


def tokenize(line: str) -> list:
    return []


def _assemble(source: str, base_addr: int):
    labels = {}
    symbol = {}

    current_addr = base_addr

    working = []

    for line_number, line in enumerate(source.splitlines()):
        tokens = tokenize(line)

        if len(tokens) == 0 or tokens[0] == ';':
            # Empty or comment only line
            continue

        if tokens[0] == '@':
            # Label definition
            label = tokens[1]
            if tokens[2] == ":":
                labels[label] = current_addr
                print(f"Added label {label} at {labels[label]}")
            elif tokens[2] == "=":
                labels[label] = tokens[3]
            else:
                raise RuntimeError(f"Malformed label on line {line_number + 1}: {line}")
        if tokens[0] == '%':
            # Symbols are preceeded by '%'
            symbol[tokens[1]] = tokens[2]
        elif tokens[0] == "check_flag":
            check_flag_cmds = {
                "clear": 0x2,
                "set": 0x3
            }
            if tokens[1] in check_flag_cmds:
                condition = check_flag_cmds[tokens[1]]
            else:
                condition = int(tokens[1], 16)

            label_index = 3
            if tokens[2] == '%':
                if tokens[3] not in symbol:
                    raise RuntimeError(f"Undefined symbol on line {line_number + 1} -  {tokens[2]}: {line}")
                else:
                    flag = symbol[tokens[3]]
                    label_index = 4
            else:
                flag = tokens[2]

            label = tokens[label_index] + tokens[label_index + 1]

            # Add the command and bump up the current address
            working.append([current_addr, 0x2d, 0x8, flag, condition, label])
            current_addr += 8
        elif tokens[0] == "remove_trigger":
            if tokens[1] == '%':
                if tokens[2] not in symbol:
                    raise RuntimeError(f"Undefined symbol on line {line_number + 1} -  {tokens[2]}: {line}")
                else:
                    trigger = Uint16(symbol[tokens[2]])
            else:
                trigger = Uint16(tokens[1])
            working.append([current_addr, 0x2e, 0x4, trigger])
            current_addr += 4
        elif tokens[0] == "update_npc":
            update_npc_cmds = {
                "hide": 0x2,
                "remove_collision": 0x4
            }
            if tokens[1] in update_npc_cmds:
                action = update_npc_cmds[tokens[1]]
            else:
                action = int(tokens[1], 16)

            if tokens[2] == '%':
                if tokens[3] not in symbol:
                    raise RuntimeError(f"Undefined symbol on line {line_number + 1} -  {tokens[2]}: {line}")
                else:
                    npc = symbol[tokens[3]]
            else:
                npc = tokens[2]

            # Add the command and bump up the current address
            working.append([current_addr, 0x30, 0x4, action, npc])
            current_addr += 4
        elif tokens[0] == "db":
            verbatim = [current_addr]
            for index in range(1, len(tokens)):
                if tokens[index] == ';':
                    break
                verbatim.append((tokens[index]))
            working.append(verbatim)
            current_addr += verbatim[2]
        elif tokens[0] == "event_end":
            working.append([current_addr, 0x0, 0x4, 0xff, 0xff])
            current_addr += 4

    assembled = []
    for pcmd in working:
        cmd = []
        for index in range(1, len(pcmd)):
            partial = pcmd[index]
            if isinstance(partial, str) and partial[0] == '@':
                label = partial[1:]
                if label not in labels:
                    raise RuntimeError(f"Undefined label: {label}")
                partial = Uint32(labels[label])

            if isinstance(partial, Uint16):
                cmd.extend(partial.bytes())
            elif isinstance(partial, Uint32):
                cmd.extend(partial.bytes())
            else:
                cmd.append(partial)
        assembled.append(cmd)

    return assembled


def assemble(source: str, base_addr: int):
    labels = {}
    symbols = {}

    current_addr = base_addr

    working = []
    for line_number, line in enumerate(source.splitlines()):
        tokens = TokenStream(line)

        token = tokens.next()
        if token is None or isinstance(token, CommentToken):
            # Empty or comment only line
            continue

        if isinstance(token, LabelToken):
            label = token
            token = tokens.next()
            if isinstance(token, ColonToken):
                labels[label] = current_addr
            elif isinstance(token, NumberToken):
                labels[label] = token
            else:
                print(f"Syntax error on line {line_number + 1}: line")
        elif isinstance(token, SymbolToken):
            symbol = token
            value = tokens.next()
            if isinstance(value, NumberToken):
                symbols[symbol] = value
            else:
                print(f"Syntax error on line {line_number + 1}: line")


def main():
    test = """
    ; Flags we want to check
    %watched_bridge_credits 0x29
    %airship_visible 0x15
    %have_chime 0x1f
    
    ; Events to clear based on flags
    %bridge_credits 0xfa6
    %raise_airship 0x138e               ; Some comment after the line
    
    check_flag clear %watched_bridge_credits .BridgeCreditsWatched
    remove_trigger %bridge_credits

    .BridgeCreditsWatched:
    check_flag clear %airship_visible .ChimeCheck
    remove_trigger %raise_airship
    
    .ChimeCheck:
    check_flag set %have_chime .PostChimeThing

    db 0x2f 0x8 0x0 0x0 0xff 0xb8 0x38 0x2
    
    .PostChimeThing:
    update_npc remove_collision 0x0
    update_npc remove_collision 0x1
    update_npc remove_collision 0x2
    update_npc remove_collision 0x3
    update_npc remove_collision 0x4
    update_npc remove_collision 0x5
    
    event_end
     
    """

    out = assemble(test, 0x80079a8)


if __name__ == "__main__":
    main()
