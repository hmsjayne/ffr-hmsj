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

from collections import namedtuple

from doslib.item import Item
from doslib.items import Items

PlacementDetails = namedtuple("Placement",
                              ['source', 'type', 'sprite', 'movable', 'zone', 'map_id', 'index', 'sprite_index',
                               'ship_x', 'ship_y', 'airship_x', 'airship_y', 'reward', 'reward_text_id',
                               'plot_flag', 'plot_item', 'extra'])


# noinspection PyProtectedMember
class Placement(object):
    def __init__(self):
        self._placement_list = Placement._parse_data("data/KeyItemPlacement.tsv")

    def all_placements(self) -> list:
        return self._placement_list

    def update_gear(self, reward: str, gear: Item):
        placements = []
        free_flag_index = 0x28
        for placement in self._placement_list:
            if placement.reward == reward:
                item_type = Items.name_to_index(gear.item_type)
                item_id = gear.id
                gear = placement._replace(
                    reward=f"free_{reward}",
                    plot_flag=free_flag_index,
                    plot_item=None,
                    extra=f"give_item_ex {hex(item_type)} {hex(item_id)}"
                )
                placements.append(gear)
            else:
                if placement.reward.startswith("free_"):
                    free_flag_index += 1
                placements.append(placement)
        self._placement_list = placements

    def update_placements(self, clingo_placements: tuple):
        # To make this easier, we'll create two lookup tables - one for sources and the other for rewards
        by_source = {}
        by_reward = {}
        for placement in self._placement_list:
            by_source[placement.source] = placement
            by_reward[placement.reward] = placement

        # Now we build new placements based on what clingo said to do
        new_placements = []
        for clingo_placement in clingo_placements:
            # TODO: Figure something to do with the Caravan eventually...
            if clingo_placement.source == "caravan":
                continue
            source = by_source[clingo_placement.source]
            reward = by_reward[clingo_placement.reward]
            new_placement = source._replace(sprite=reward.sprite, movable=reward.movable, reward=reward.reward,
                                            reward_text_id=reward.reward_text_id, plot_flag=reward.plot_flag,
                                            plot_item=reward.plot_item, extra=reward.extra)
            new_placements.append(new_placement)
        self._placement_list = new_placements

    @staticmethod
    def _parse_data(data_file_path: str) -> list:
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

                    data.append(PlacementDetails(*row_data))
                else:
                    properties = line.strip().split('\t')
                    first_line = False
        return data
