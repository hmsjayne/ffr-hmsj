#  Copyright 2020 Nicole Borrelli
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


def decode_permission_string(perms: str) -> int:
    char_bits = "fKtNmMrRwWbB"
    char_to_bitmask = {}
    for index in range(0, len(char_bits)):
        bit = (1 << int(index / 2)) << (index % 2 * 8)
        char_to_bitmask[char_bits[index]] = bit

    perm = 0x0
    for index in range(0, len(perms)):
        perm = perm | char_to_bitmask[perms[index]]
    return perm


def load_tsv(data_file_path: str) -> list:
    data = []
    properties = None
    with open(data_file_path, "r") as data_file:
        first_line = True
        for line in data_file.readlines():
            if not first_line:
                values = line.strip().split('\t')
                row_data = []
                for index, key in enumerate(properties):
                    if index < len(values):
                        if len(values[index]) == 0 or values[index] == "None":
                            value = None
                        elif values[index].lower() in ["true", "false"]:
                            value = values[index].lower() == "true"
                        else:
                            try:
                                value = int(values[index], 0)
                            except ValueError:
                                value = values[index]
                        row_data.append(value)
                    else:
                        row_data.append(None)

                data.append(row_data)
            else:
                properties = line.strip().split('\t')
                first_line = False
    return data
