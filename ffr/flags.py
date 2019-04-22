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


class Flags(object):
    def __init__(self, flags_str: str):
        self.encounters = None
        self.default_party = None

        self.magic = None
        self.treasures = None
        self.key_item_shuffle = None
        self.XP_mult = 1.0

        self.debug = None

        for flag in flags_str.split():
            if flag == "K":
                self.key_item_shuffle = "shuffle"
            elif flag == "Et":
                self.encounters = "toggle"
            elif flag == "Ms":
                self.magic = "shuffle"
            elif flag == "Ts":
                self.treasures = "shuffle"
            elif flag == "-who":
                self.default_party = "random"
            elif flag == "-hax":
                self.debug = "iddqd"
            elif flag[:2] == "XP":
                self.XP_mult *= float(flag.split("=")[1])