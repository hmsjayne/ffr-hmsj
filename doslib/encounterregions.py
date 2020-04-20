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

from doslib.rom import Rom
from stream.outputstream import OutputStream


class EncounterRegions(object):
    def __init__(self, rom: Rom):
        self.overworld_regions = []
        ow_stream = rom.open_bytestream(0x2170E0, 0x217300 - 0x2170E0)
        while not ow_stream.is_eos():
            # Each region has 8 encounters which we'll load into an array
            encounter_list = []
            for index in range(0, 8):
                encounter_list.append(ow_stream.get_u8())
            self.overworld_regions.append(encounter_list)

        self.map_encounters = []
        map_stream = rom.open_bytestream(0x2177CC, 0x217AD4 - 0x2177CC)
        while not map_stream.is_eos():
            # Each region has 8 encounters which we'll load into an array
            encounter_list = []
            for index in range(0, 8):
                encounter_list.append(map_stream.get_u8())
            self.map_encounters.append(encounter_list)

    def get_patches(self) -> dict:
        overworld_stream = OutputStream()
        for region in self.overworld_regions:
            for encounter in region:
                overworld_stream.put_u8(encounter)
        return {
            0x2170E0: overworld_stream.get_buffer()
        }
