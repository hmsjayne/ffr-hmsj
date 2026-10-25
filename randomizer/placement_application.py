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
from randomizer.game_data import VehiclePosition


def apply_placements(placement, maps, vehicle_starts: dict) -> None:
    """Apply key-item placements to maps and vehicle starts in place."""
    for ki_placement in placement.all_placements():
        # If this is the airship, reset where it comes out.
        if ki_placement.reward == "airship":
            vehicle_starts["airship"] = VehiclePosition(x=ki_placement.airship_x, y=ki_placement.airship_y)
        elif ki_placement.reward == "ship":
            vehicle_starts["ship"] = VehiclePosition(x=ki_placement.ship_x, y=ki_placement.ship_y)

        # This is really just for the desert, but this feels safer, somehow?
        if ki_placement.map_id is None:
            continue

        if ki_placement.type == 'npc':
            npc_map = maps.get_map(ki_placement.map_id)
            npc_map.npcs[ki_placement.index].sprite_id = ki_placement.sprite

            # Some sprites weren't designed to move, so hold them still.
            if not ki_placement.movable:
                npc_map.npcs[ki_placement.index].move_speed = 0

            # Princess Sara is both in Cornelia Castle, where she gives the player the lute, and in the
            # Temple of Fiends, having been kidnapped by Garland at the start of the game.
            if ki_placement.source == "sara":
                tof_map = maps.get_map(0x1f)
                princess_sara_index = tof_map.find_npc(0x0)
                tof_map.npcs[princess_sara_index].sprite_id = ki_placement.sprite
                tof_map.npcs[princess_sara_index].move_speed = 0

        elif ki_placement.type == 'chest':
            chest_map = maps.get_map(ki_placement.map_id)
            chest, sprite = chest_map.get_event_chest(ki_placement.index)
            chest_map.chests.remove(chest)
            chest_map.sprites.remove(sprite)

            chest_npc = Npc()
            chest_npc.identifier = 0x2
            chest_npc.in_room = 0x1
            chest_npc.x_pos = sprite.x_pos
            chest_npc.y_pos = sprite.y_pos
            chest_npc.move_speed = 0
            chest_npc.event = sprite.event

            if ki_placement.map_id in [0x38, 0x5b, 0x1e]:
                # Use a chest in Cornelia, Marsh, and the mermaid floor in Sea.
                chest_npc.sprite_id = 0xc7
            else:
                chest_npc.sprite_id = ki_placement.sprite
            chest_map.npcs.append(chest_npc)
        else:
            raise RuntimeError(f"Unknown placement type: {ki_placement.type} at {ki_placement.source}")
