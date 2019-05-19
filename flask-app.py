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
from randomizer.flags import Flags
from randomize import randomize_rom

app = Flask(__name__)


@app.route('/')
def root():
    return app.send_static_file('index.html')


@app.route('/randomize', methods=['POST'])
def randomize():
    uploaded_rom = request.files['rom']
    rom = Rom(data=uploaded_rom.read())
    flags_string = request.form['flags']
    seed = request.form['seed']

    rom = randomize_rom(rom, Flags(flags_string), seed)

    filename = uploaded_rom.filename
    index = filename.rfind(".gba")
    if index < 0:
        return f"Bad filename: {filename}"
    filename = f"{filename[0:index]}.{seed}.gba"

    response = make_response(rom.rom_data)
    response.headers['Content-Type'] = "application/octet-stream"
    response.headers['Content-Disposition'] = f"inline; filename={filename}"
    return response