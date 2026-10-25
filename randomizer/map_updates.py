#  Copyright 2026 HMS Jayne contributors
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

from doslib.map import Npc


def remove_tiles_with_event(tiles: list, event: int) -> list:
    return [tile for tile in tiles if tile.event != event]


def prevent_canal_soft_lock(overworld):
    # The easiest way to do this is create an NPC and place them on top of the canal spot.
    # This prevents walking across and the airship landing there.
    canal_splash = Npc()
    canal_splash.identifier = 0x2
    canal_splash.in_room = 0x1
    canal_splash.x_pos = 95
    canal_splash.y_pos = 157
    canal_splash.move_speed = 0
    canal_splash.event = 0x1f62
    canal_splash.sprite_id = 0xC6
    overworld.npcs.append(canal_splash)


def map_updates(maps):
    maps_with_doors = [
        0x06,  # Elven Castle
        0x38,  # Castle Cornelia 1F
    ]

    # There are two events (in vanilla) for mystic key locked doors.
    # - 0x1f4a: This door has been bound by the mystic key.
    # - 0x23cd: The treasure house has been bound by the mystic key.
    # In order to simplify some of the logic, change the 3 instances of the second to the first
    # since it's more generic.
    for map_id in maps_with_doors:
        door_map = maps.get_map(map_id)
        for sprite in door_map.sprites:
            if sprite.event == 0x23cd:
                sprite.event = 0x1f4a

    # In the vanilla game, you grab the Star Ruby from behind the Vampire, leave Earth Cave,
    # visit Sarda, get the Rod, and come back to open the plate. In theory, in HMS Janye you
    # could find the Rod behind the Vampire. In this case the event on the Earth Plate would
    # be the basic "You sense something evil" event rather than the event that will break it
    # open if you have the Rod.
    #
    # To fix this, we always have the Rod script on the tablet, and just have a check in that
    # script for the Rod, printing the "evil" text if the player doesn't have it.
    maps.get_map(0x3).npcs[0xe].event = 0x139c

    # There could be fewer bats... This also makes room for features in other maps.
    bat_mania_maps = [
        0x2,  # Earth B2
        0x4,  # Earth B4
    ]

    for map_id in bat_mania_maps:
        bat_map = maps.get_map(map_id)
        fewer_bats = []
        for index, npc in enumerate(bat_map.npcs):
            if npc.event == 0x200c:
                if index % 2 == 0:
                    fewer_bats.append(npc)
            else:
                fewer_bats.append(npc)
        bat_map.npcs = fewer_bats

    prevent_canal_soft_lock(maps.get_map(0x0))

    # Citadel of trials -- can enter w/o the stolen Crown
    citadel_of_trials = maps.get_map(0x4d)
    citadel_of_trials.npcs = []
    citadel_of_trials.tiles = remove_tiles_with_event(citadel_of_trials.tiles, 0x23d0)
