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


def pparse(source: str) -> str:
    symbol_table = {}
    working = []

    lines = source.splitlines()
    line_number = 0
    while line_number < len(lines):
        line = lines[line_number]

        tokens = line.split()
        if line.startswith('#'):
            if tokens[0] == "#ifdef":
                if tokens[1] not in symbol_table:
                    ifdef_count = 1
                    while ifdef_count > 0 and line_number < len(lines):
                        line_number += 1
                        line = lines[line_number]
                        if line.startswith("#ifdef"):
                            ifdef_count += 1
                        elif line.startswith("#endif"):
                            ifdef_count -= 1
                        working.append("")
            if tokens[0] == "#define":
                symbol_name = tokens[1]
                value = line[line.index(symbol_name) + len(symbol_name) + 1:]
                while value.endswith("\\"):
                    line_number += 1
                    value = f"{value[0:len(value) - 1]}\n{lines[line_number]}"
                symbol_table[symbol_name] = value
        else:
            outline = ""
            for token in tokens:
                if token in symbol_table:
                    outline += f"{symbol_table[token]} "
                else:
                    outline += f"{token} "
            working.append(outline)

        line_number += 1

    return "\n".join(working)
