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

import datetime
import sys


def main(argv):
    with open('datatype.def', 'r') as data_type_def:
        lines = data_type_def.readlines()

    modules = dict()
    current_module = None
    current_class = None

    for line_number, line in enumerate(lines):
        clean = line.lstrip().rstrip()
        if len(clean) > 0 and clean[0] != '#':
            if clean.startswith("module:"):
                current_module = clean.split(":")[1].lstrip().rstrip()

                if current_module not in modules:
                    modules[current_module] = dict()
            elif clean.startswith("class:"):
                current_class = clean.split(":")[1].lstrip().rstrip()

                if current_module is None:
                    raise RuntimeError(f"Malformed datatype.def file at line {line_number + 1}: {line}; "
                                       f"Expected module before class")
                module = modules[current_module]
                if current_class not in module:
                    module[current_class] = []
            elif current_module is not None and current_class is not None:
                module = modules[current_module]
                module[current_class].append(clean)
            else:
                raise RuntimeError(f"Malformed datatype.def file at line {line_number + 1}: {line}")

    for module in modules:
        current_module = modules[module]

        with open(f"{module}.py", 'w') as module_file:
            module_file.writelines(f"""#  Licensed under the Apache License, Version 2.0 (the "License");
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
#
#  This file is generated by build_types.py from datatype.def.
#
#  DO NOT EDIT THIS FILE DIRECTLY. Update "datatype.def" and rerun "build_types.py"
#
#  Generated on {datetime.datetime.now().strftime("%Y-%m-%d %H:%M")}

from stream.input import Input
from stream.output import Output


""")

            for a_class in current_module:
                current_class = current_module[a_class]

                init_text = ""
                write_text = ""
                for field_text in current_class:
                    field_data = field_text.split(",")
                    field_name = field_data[0].lstrip().rstrip()
                    field_size = field_data[1].lstrip().rstrip()

                    # First, text for __init__ block.
                    init_text += f"        self.{field_name} = stream.get_u{field_size}()\n"

                    # Next, text for write block.
                    write_text += f"        stream.put_u{field_size}(self.{field_name})\n"

                # Build the full class as a string
                class_lines = [
                    f"class {a_class}(object):\n",
                    f"    def __init__(self, stream: Input):\n{init_text}\n",
                    f"    def write(self, stream: Output):\n{write_text}\n\n"
                ]
                module_file.writelines(class_lines)


if __name__ == "__main__":
    main(sys.argv[1:])