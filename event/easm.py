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

from event import codegen
from event.codegen import simple_gen
from event.parseinputstring import ParseInputString
from event.tokens import *

# The grammar for `easm` is very simple, and is defined in the dict here.
from stream.outputstream import OutputStream

GRAMMAR = {
    # Here we define mappings of strings to terminal tokens.
    # If a string is not defined here, it will likely cause a SyntaxError exception.
    "end_event": EndEventToken([0x0, 0x4, 0xff, 0xff]),
    "nop": NopToken([0x1, 0x4, 0xff, 0xff]),
    "load_text": LoadTextToken("load_text"),
    "close_dialog": CloseDialogToken("close_dialog"),
    "jump": JumpToken("jump"),
    "jump_chest_empty": JumpChestEmptyToken("jump_chest_empty"),
    "music": MusicToken("music"),
    "set_repeat": SetRepeatToken("set_repeat"),
    "repeat": RepeatToken("repeat"),
    "show_dialog": ShowDialogToken([0x27, 0x4, 0x0, 0xff]),
    "set_flag": SetFlagToken("set_flag"),
    "check_flag": CheckFlagToken("check_flag"),
    "remove_trigger": RemoveTriggerToken("remove_trigger"),
    "npc_update": NpcUpdateToken("npc_update"),
    "set_npc_event": SetNpcEventToken("set_npc_event"),
    "remove_all": RemoveAllToken([0x36, 0x4, "$(u:0)"]),
    "give_item": GiveItemToken([0x37, 0x4, 0x0, "$0"]),
    "take_item": TakeItemToken([0x37, 0x4, 0x1, "$0"]),
    "check_item": CheckItemToken("check_item"),
    "jump_by_dir": JumpByDirToken("jump_by_dir"),

    # Conditional jumps
    "jz": JzToken(0x2),
    "jnz": JnzToken(0x3),

    # Here are various other keywords that are command specific.
    "top": LoadTextTopToken(0x0),
    "bot": LoadTextBottomToken(0x1),
    "wait": CloseDialogWaitToken(0x1),
    "auto": CloseDialogAutoToken(0x0),

    #
    # Define various non-terminal tokens here.
    #
    "$$value$$": (SymbolToken(), NumberToken()),
    "$$cond$$": (JzToken(), JnzToken()),

    # Language constructs are here.
    "$$def_label": LabelToken("def_label"),
    LabelToken: [LabelToken(), (ColonToken(), "$$value$$")],
    "$$def_symbol": SymbolToken("def_symbol"),
    SymbolToken: [SymbolToken(), "$$value$$"],

    #
    # Define the structure of each command here.
    # Commands that don't match the patterns here will raise a SyntaxError exception.
    #
    EndEventToken: None,
    LoadTextToken: [(LoadTextTopToken(), LoadTextBottomToken()), "$$value$$"],
    CloseDialogToken: [(CloseDialogAutoToken(), CloseDialogWaitToken())],
    JumpToken: [LabelToken()],
    JumpChestEmptyToken: [LabelToken()],
    MusicToken: ["$$value$$", "$$value$$"],
    SetRepeatToken: ["$$value$$"],
    RepeatToken: ["$$value$$", LabelToken()],
    ShowDialogToken: None,
    SetFlagToken: ["$$value$$"],
    CheckFlagToken: ["$$value$$", "$$cond$$", LabelToken()],
    RemoveTriggerToken: ["$$value$$"],
    NpcUpdateToken: ["$$value$$", "$$value$$"],
    SetNpcEventToken: ["$$value$$", "$$value$$"],
    RemoveAllToken: ["$$value$$"],
    GiveItemToken: ["$$value$$"],
    TakeItemToken: ["$$value$$"],
    CheckItemToken: ["$$value$$", JzToken(), LabelToken()],
    JumpByDirToken: [LabelToken(), LabelToken(), LabelToken()],
    # The one special case is the `db` (define bytes).
    # This command is handled separately by the parser, because it is essentially a request to insert the
    # bytes that proceed it verbatim into the output. Because the command can be followed by any number
    # of bytes, it's easiest to just not try to worry about coding that into the grammar.
    "db": RawCommandToken("_cmd_db"),
}


class DuplicateSymbolError(RuntimeError):
    def __init__(self, name, line, line_number):
        super().__init__(f"Duplicate symbol defined: '{name}' on line {line_number}: {line}")


class SymbolNotDefinedError(RuntimeError):
    def __init__(self, name, line, line_number):
        super().__init__(f"Undefined symbol '{name}' on line {line_number}: {line}")


class ParserSyntaxError(RuntimeError):
    def __init__(self, token, line, line_number):
        super().__init__(f"Unexpected token '{token}' on line {line_number}: {line}")


class UndefinedLabel(RuntimeError):
    def __init__(self, label: str):
        super().__init__(f"Undefined label: '{label}'")


def def_symbol(parameters: list, symbol_table: dict):
    name = parameters[0]
    value = parameters[1]

    if name in symbol_table:
        raise DuplicateSymbolError(name)

    if isinstance(value, SymbolToken):
        value = symbol_table[value]
    symbol_table[name] = value
    return None


def parse(source: str, base_addr: int, debug=False) -> bytearray:
    symbol_table = {}
    icode = []
    current_addr = base_addr

    for line_number, line in enumerate(source.splitlines()):
        tokens = TokenStream(line_number, line)

        token = tokens.next()
        if token is None:
            # Empty or comment only line
            continue

        if isinstance(token, RawCommandToken):
            parameters = []
            token = tokens.expect(GRAMMAR["$$value$$"])
            while token is not None:
                parameters.append(token)
                token = tokens.expect(GRAMMAR["$$value$$"])

            icode.append(parameters)
            current_addr += parameters[1]
        else:
            # Save the op name
            op_name = token

            if type(token) not in GRAMMAR:
                raise ParserSyntaxError(token, line, line_number)
            match = GRAMMAR[type(token)]
            if isinstance(match, dict):
                rule_set = match["rule"]
            else:
                rule_set = match

            parameters = []

            if rule_set is not None:
                for rule in rule_set:
                    if isinstance(rule, str) and rule.startswith("$$"):
                        rule = GRAMMAR[rule]
                    token = tokens.expect(rule)

                    if token is None:
                        raise ParserSyntaxError(token, line, line_number)

                    if isinstance(op_name, SymbolToken):
                        parameters.append(token)
                    else:
                        if isinstance(token, SymbolToken):
                            if token in symbol_table:
                                parameters.append(symbol_table[token])
                            else:
                                raise SymbolNotDefinedError(token, line, line_number)
                        else:
                            parameters.append(token)

                verify_end = tokens.expect(CommentToken())
            else:
                verify_end = tokens.expect(CommentToken())

            if op_name == "def_symbol" or op_name == "def_label":
                name = parameters[0]
                value = parameters[1]
                if name in symbol_table:
                    raise DuplicateSymbolError(name, line, line_number)

                if isinstance(value, ColonToken):
                    value = current_addr
                symbol_table[name] = value
            else:
                if isinstance(op_name, list):
                    output = simple_gen(op_name, parameters)
                else:
                    method = getattr(codegen, op_name)
                    output = method(parameters)

                if output is not None:
                    icode.append(output)
                    current_addr += output[1]

    # At this point, all of the intermediate code is built and the only thing left is to resolve
    # the left over symbols, which will all bel labels.
    bytecode = OutputStream()
    for code in icode:
        txt = ""
        for bd in code:
            if isinstance(bd, LabelToken):
                label = bd
                if label not in symbol_table:
                    raise UndefinedLabel(label)
                bytecode.put_u32(symbol_table[label])
                txt += f"{label} ({hex(symbol_table[label])}) "
            else:
                txt += f"{hex(bd)} "
                bytecode.put_u8(bd)
        if debug:
            print(txt)

    # Done!
    return bytecode.get_buffer()


class TokenStream(object):
    def __init__(self, line_number: int, line: str):
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

            if isinstance(token, CommentToken):
                # If it's a comment, just skip over it to the `None` that's after it.
                self._index += 1
                token = self.peek()
        return token

    def expect(self, token_types):
        allowed_types = []
        if isinstance(token_types, tuple):
            for token_type in token_types:
                allowed_types.append(type(token_type))
        else:
            allowed_types.append(type(token_types))

        token = self.next()

        if token is not None:
            if type(token) not in allowed_types:
                print(f"{type(token)} was not in {allowed_types}")
                raise ParserSyntaxError(token, self._input_line, self._line_number)

        return token

    def reset(self):
        self._index = 0

    def _tokenize(self, line: str) -> list:
        tokens = []

        current = ParseInputString(line)
        char = current.getc()
        while char is not None:
            if char.isspace():
                # Ignore whitespace...
                pass
            elif char.isalpha():
                current.ungetc()
                keyword = current.get_alphanum_str(['_'])
                if keyword not in GRAMMAR:
                    raise RuntimeError(f"Unknown keyword: {keyword}")
                token = GRAMMAR[keyword]
                tokens.append(token)
            elif char.isdigit():
                # Numbers are all ints and just parsed by the stream - makes this easier
                current.ungetc()
                tokens.append(NumberToken(current.get_int()))
            elif char == '.':
                if current.peek().isalpha():
                    if len(tokens) == 0:
                        tokens.append(GRAMMAR["$$def_label"])
                    tokens.append(LabelToken(current.get_alphanum_str(['_'])))
                else:
                    raise RuntimeError(f"Illegal label definition, starts with: {current.peek()}")
            elif char == '%':
                if current.peek().isalpha():
                    if len(tokens) == 0:
                        tokens.append(GRAMMAR["$$def_symbol"])
                    tokens.append(SymbolToken(current.get_alphanum_str(['_'])))
                else:
                    raise RuntimeError(f"Illegal label definition, starts with: {current.peek()}")
            elif char == ':':
                tokens.append(ColonToken(":"))
            elif char == ";":
                comment = ";"
                while current.peek() is not None:
                    comment += current.getc()
                tokens.append(CommentToken(comment))
            elif char == "$":
                raise RuntimeError(f"'$' characters are reserved for the assembler and may not be used.")
            else:
                # Symbols are single characters
                tokens.append(char)

            char = current.getc()

        return tokens
