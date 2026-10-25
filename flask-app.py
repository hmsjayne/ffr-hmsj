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

from pathlib import Path

from flask import Flask, make_response, request
from ips_util import Patch

from randomizer.api import randomize_rom
from randomizer.legacy_flags import LegacyFlagsError, parse_legacy_flags
from randomizer.options import DEFAULT_OPTIONS
from randomizer.seed import InvalidSeedError, normalize_seed
from randomizer.share import build_filename

app = Flask(__name__, static_folder="static", static_url_path='')


@app.route('/')
def root():
    return app.send_static_file('index.html')


@app.route('/patch', methods=['POST'])
def create_patch():
    rom_upload = request.files.get('rom')
    if rom_upload is None:
        return "Please select a ROM.", 400

    try:
        seed = normalize_seed(request.form.get('seed', ''))
    except InvalidSeedError as exc:
        return str(exc), 400

    flags_string = request.form.get('flags', '')
    if flags_string:
        try:
            options = parse_legacy_flags(flags_string).options
        except LegacyFlagsError as exc:
            return str(exc), 400
    else:
        options = DEFAULT_OPTIONS

    rom_data = bytearray(rom_upload.read())
    result = randomize_rom(rom_data, seed, options)
    patch = Patch.create(rom_data, result.rom_data)
    filename = build_filename(seed, options, base_name=Path(rom_upload.filename).stem, extension="ips")

    response = make_response(patch.encode())
    response.headers['Content-Type'] = "application/octet-stream"
    response.headers['Content-Disposition'] = f"inline; filename={filename}"
    return response


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    # Run the Flask app
    app.run(port=8080)
