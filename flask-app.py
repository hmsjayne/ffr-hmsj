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
from urllib import parse

from flask import Flask, request, make_response
from ips_util import Patch

from doslib.rom import Rom
from randomize import randomize_rom, get_filename, gen_seed
from randomizer.flags import Flags

app = Flask(__name__)


@app.route('/')
def root():
    return app.send_static_file('index.html')


@app.route('/test')
def patch_ui():
    return app.send_static_file('test.html')


@app.route('/hmslogo.jpg')
def hms_logo():
    return app.send_static_file('hmslogo.jpg')


@app.route('/discord.png')
def discord():
    return app.send_static_file('discord.png')


@app.route('/github.png')
def github():
    return app.send_static_file('github.png')


@app.route('/randomize', methods=['POST'])
def randomize():
    uploaded_rom = request.files['rom']
    rom = Rom(data=uploaded_rom.read())
    flags_string = request.form['flags']
    flags = Flags(flags_string)
    rom_seed = gen_seed(request.form['seed'])

    rom = randomize_rom(rom, flags, rom_seed)

    filename = uploaded_rom.filename
    index = filename.lower().rfind(".gba")
    if index < 0:
        return f"Bad filename: {filename}"
    filename = parse.quote(get_filename(filename, flags, rom_seed))

    response = make_response(rom.rom_data)
    response.headers['Content-Type'] = "application/octet-stream"
    response.headers['Content-Disposition'] = f"inline; filename={filename}"
    return response


@app.route('/patch', methods=['POST'])
def create_patch():
    vanilla_rom = Rom("ff-dos.gba")
    flags_string = request.form['flags']
    flags = Flags(flags_string)
    rom_seed = gen_seed(request.form['seed'])

    rom = randomize_rom(vanilla_rom, flags, rom_seed)

    gba_name = get_filename("ff-dos", flags, rom_seed)
    filename = parse.quote(gba_name[:len(gba_name) - 4] + ".ips")

    patch = Patch.create(vanilla_rom.rom_data, rom.rom_data)
    response = make_response(patch.encode())
    response.headers['Content-Type'] = "application/octet-stream"
    response.headers['Content-Disposition'] = f"inline; filename={filename}"
    return response
