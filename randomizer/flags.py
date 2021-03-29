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


class Flags(object):
    def __init__(self, parsed=None):
        if parsed is not None:
            self.no_shuffle = parsed.no_shuffle
            self.standard_shops = parsed.standard_shops
            self.standard_treasure = parsed.standard_treasure
            self.default_start_gear = parsed.default_start_gear
            self.debug = parsed.debug
            self.new_items = parsed.new_items
            self.boss_shuffle = parsed.boss_shuffle

            if parsed.exp_mult is not None:
                self.scale_levels = 1.0 / parsed.exp_mult
            else:
                self.scale_levels = 1.0
        else:
            self.no_shuffle = False
            self.standard_shops = False
            self.standard_treasure = False
            self.default_start_gear = False
            self.new_items = False
            self.debug = False
            self.boss_shuffle = False
            self.scale_levels = 1.0

    def encode(self) -> str:
        encoded = ""
        if not self.no_shuffle:
            encoded += "K"
        if not self.standard_shops:
            encoded += "S"
        if not self.standard_treasure:
            encoded += "T"
        if not self.default_start_gear:
            encoded += "G"
        if not self.boss_shuffle:
            encoded += "B"
        if self.new_items:
            encoded += "Ni"
        if self.debug:
            encoded += "\\u819a"
        encoded += str(int((self.scale_levels * 10)))
        return encoded

    def __str__(self):
        out = []
        for property, value in vars(self).items():
            out.append(f"{property}={value}")
        return "[Flags:" + ",".join(out) + "]"
