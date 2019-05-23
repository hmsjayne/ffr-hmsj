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

# Event Pre-Processor


class PreProcessCode(object):
    def __init__(self, source: str):
        self._source = source.splitlines()
        self._line_no = 0

    def get_line_no(self):
        return self._line_no

    def get_line(self, line_no: int = None) -> str:

        if line_no is None:
            line_no = self._line_no
            self._line_no += 1

        if line_no < len(self._source):
            line = self._source[line_no].strip()
        else:
            line = None
        return line

    def unget_line(self):
        if self._line_no > 0:
            self._line_no -= 1


def pparse(source: str) -> str:
    ppcode = PreProcessCode(source)
    processed_code = do_parse(ppcode, {})
    return "\n".join(processed_code)


def do_parse(source: PreProcessCode, symbol_table: dict, start_line: int = None, include_output: bool = True) -> list:
    working = []
    else_block = False

    line = source.get_line()
    while line is not None:
        tokens = line.split()
        if line.startswith('#'):
            if tokens[0] == "#ifdef":
                process_output = tokens[1] in symbol_table
                nested = do_parse(source, symbol_table, source.get_line_no(), process_output)
                working.extend(nested)
            elif tokens[0] == "#ifndef":
                process_output = tokens[1] not in symbol_table
                print(f"{tokens[1]} -> {process_output}")
                nested = do_parse(source, symbol_table, source.get_line_no(), process_output)
                working.extend(nested)
            elif tokens[0] == "#else":
                if not else_block:
                    include_output = not include_output
                    else_block = True
                else:
                    raise RuntimeError(f"Multiple #else tags in an #if block")
            elif tokens[0] == "#endif":
                if start_line is not None:
                    return working
                else:
                    raise RuntimeError(f"#endif without #if")
            elif tokens[0] == "#define":
                symbol_name = tokens[1]
                value = line[line.index(symbol_name) + len(symbol_name) + 1:]
                while value.endswith("\\"):
                    value = f"{value[0:len(value) - 1]}\n{source.get_line()}"
                symbol_table[symbol_name] = value
        elif include_output:
            outline = ""
            for token in tokens:
                if token in symbol_table:
                    outline += f"{symbol_table[token]} "
                else:
                    outline += f"{token} "
            working.append(outline)
        else:
            # Not including output due to an #ifdef/#ifndef condition
            pass

        # Next line of input
        line = source.get_line()

    if start_line is None:
        return working
    else:
        raise RuntimeError(f"End of input in #if block - started on line {start_line - 1}\n"
                           f"{source.get_line(start_line - 1)}")
