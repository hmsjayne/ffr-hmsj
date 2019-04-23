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
        if self._index < len(self._data):
            self._index += 1
            return self._data[self._index - 1]
        else:
            return None

    def ungetc(self):
        if self._index > 0:
            self._index -= 1

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


def tokenize(line: str) -> list:
    tokens = []

    input = InputString(line)
    char = input.getc()
    while char is not None:
        if char.isspace():
            # Ignore whitespace...
            pass
        elif char.isalpha():
            # Identifiers are alphanumeric, but start with a letter. They may include '_' because ... Python?
            current = ""
            while char is not None and (char.isalnum() or char == '_'):
                current += char
                char = input.getc()
            tokens.append(current)

            # Took one too many characters, potentially.
            if char is not None:
                input.ungetc()
        elif char.isdigit():
            # Numbers are all ints and just parsed by the stream - makes this easier
            input.ungetc()
            tokens.append(input.get_int())
        else:
            # Symbols are single characters
            tokens.append(char)

        char = input.getc()

    return tokens


def assemble(source: str, base_addr: int):
    labels = {}
    symbol = {}

    current_addr = base_addr

    working = []

    for line_number, line in enumerate(source.splitlines()):
        line = line.lstrip().rstrip()
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


def main():
    test = """
    ; Flags we want to check
    %watched_bridge_credits 0x29
    %airship_visible 0x15
    %have_chime 0x1f
    
    ; Events to clear based on flags
    %bridge_credits 0xfa6
    %raise_airship 0x138e
    
    check_flag clear %watched_bridge_credits @BridgeCreditsWatched
    remove_trigger %bridge_credits

    @BridgeCreditsWatched:
    check_flag clear %airship_visible @ChimeCheck
    remove_trigger %raise_airship
    
    @ChimeCheck:
    check_flag set %have_chime @PostChimeThing

    db 0x2f 0x8 0x0 0x0 0xff 0xb8 0x38 0x2
    
    @PostChimeThing:
    update_npc remove_collision 0x0
    update_npc remove_collision 0x1
    update_npc remove_collision 0x2
    update_npc remove_collision 0x3
    update_npc remove_collision 0x4
    update_npc remove_collision 0x5
    
    event_end
     
    """
    out = assemble(test, 0x80079a8)
    for cmd in out:
        line = ""
        for b in cmd:
            line += f"{hex(b)} "
        print(f"Command: {line}")


if __name__ == "__main__":
    main()
