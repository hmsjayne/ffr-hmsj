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

from flask import Flask, make_response, request
from ips_util import Patch

from randomizer.flags import Flags
from randomizer.randomize import randomize

app = Flask(__name__, static_folder="static", static_url_path='')


@app.route('/')
def root():
    return app.send_static_file('index.html')


@app.route('/patch', methods=['POST'])
def create_patch():
    patch = bytearray()
    filename = "patch.ips"

    flags_string = request.form['flags']
    rom_seed = request.form['seed']

    flags = Flags()
    flags.no_shuffle = flags_string.find("Op") != -1
    flags.standard_shops = flags_string.find("Sv") != -1
    flags.standard_treasure = flags_string.find("Tv") != -1
    flags.default_start_gear = flags_string.find("Gv") != -1
    flags.boss_shuffle = flags_string.find("B") != -1
    flags.new_items = flags_string.find("Ni") != -1

    xp_start = flags_string.find("Xp")
    if xp_start >= 0:
        xp_start += 2
        xp_str = ""
        while xp_start < len(flags_string) and flags_string[xp_start].isdigit():
            xp_str += flags_string[xp_start]
            xp_start += 1
        flags.scale_levels = 1.0 / (int(xp_str) / 10.0)

    with open("ff-dos.gba", "rb") as rom_file:
        rom_data = bytearray(rom_file.read())
        randomized_rom = randomize(rom_data, rom_seed, flags)

        patch = Patch.create(rom_data, randomized_rom)
        response = make_response(patch.encode())
        response.headers['Content-Type'] = "application/octet-stream"
        response.headers['Content-Disposition'] = f"inline; filename={filename}"
        return response
