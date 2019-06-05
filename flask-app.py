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

from flask import Flask, request, make_response

from doslib.rom import Rom
from randomize import randomize_rom, get_filename, gen_seed
from randomizer.flags import Flags

app = Flask(__name__)


@app.route('/')
def root():
    return app.send_static_file('index.html')


@app.route('/hmslogo.jpg')
def hms_logo():
    return app.send_static_file('hmslogo.jpg')


@app.route('/border.png')
def border():
    return app.send_static_file('border.png')


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
    filename = get_filename(filename, flags, rom_seed)

    response = make_response(rom.rom_data)
    response.headers['Content-Type'] = "application/octet-stream"
    response.headers['Content-Disposition'] = f"inline; filename={filename}"
    return response
