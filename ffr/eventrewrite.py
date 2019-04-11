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

from __future__ import annotations

import copy

from doslib.event import Event, EventCommand


class Reward(object):
    def __init__(self, flag: int = None, mask: int = None, item: int = None):
        if flag is not None and item is None:
            self._flag = flag
            self._mask = mask
            self._item = None
        elif flag is None and item is not None:
            self._item = item
            self._flag = None
        else:
            raise RuntimeError(f"Invalid reward: flag={hex(flag)}, mask={hex(mask)}, item={hex(item)}")

    def is_flag(self):
        return self._flag is not None

    def get_cmd(self):
        if self.is_flag():
            return EventCommand([0x2d, 0x4, self._flag, self._mask])
        else:
            return EventCommand([0x37, 0x4, 0x0, self._item])


class EventRewriter(object):
    def __init__(self, event: Event):
        self._replace_dialog = {}
        self._replace_with_pose = {}

        self._visiting_npcs = []
        self._input_event = event

        self._should_skip_dialog = True

        self._reward_cmd = EventCommand([-1, 4, 0, 0])
        self._reward_replacement = None

    def include_dialogs(self, *string_ids):
        for string_id in string_ids:
            self._replace_dialog[string_id] = string_id

    def visiting_npc(self, *sprite_indices):
        for sprite_index in sprite_indices:
            self._visiting_npcs.append(sprite_index)

    def rewrite_dialog(self, original_dialog: int, replacement_dialog: int):
        self._replace_dialog[original_dialog] = replacement_dialog

    def replace_set_frame_with_pose(self, npc_index: int, frame: int, pose: int):
        if npc_index not in self._replace_with_pose:
            self._replace_with_pose[npc_index] = {}
        self._replace_with_pose[npc_index][frame] = pose

    def replace_reward(self, original: Reward, replacement: Reward):
        self._reward_cmd = original.get_cmd()
        self._reward_replacement = replacement

    def rewrite(self) -> Event:
        new_commands = []

        for command in self._input_event.commands:
            op = command.cmd()

            # To simplify processing, decide whether dialog commands are going to be included or not
            # before processing any of the commands.
            # If the dialog is going to be included, pick out the text it should be replaced with.
            # This might be the same dialog, to keep it, but this keeps the logic simple.
            if op == 0x5:
                str_id = command.get_u16(2)
                if str_id in self._replace_dialog:
                    self._should_skip_dialog = False
                    command.put_u16(2, self._replace_dialog[str_id])
                else:
                    self._should_skip_dialog = True

            if op in EventRewriter.DIALOG_COMMANDS:
                if self._should_skip_dialog:
                    new_commands.extend(self._cmd_as_nop(command))
                else:
                    new_commands.append(command)
            elif op == EventRewriter.SET_ANI_FRAME_CMD:
                npc_index = command[2]
                if npc_index in self._visiting_npcs:
                    if npc_index in self._replace_with_pose:
                        poses = self._replace_with_pose[npc_index]
                        ani_frame = command[3]
                        if ani_frame in poses:
                            pose_cmd_data = [
                                EventRewriter.SET_POSE_CMD,
                                0x4,
                                npc_index,
                                poses[ani_frame]
                            ]
                            pose_cmd = EventCommand(pose_cmd_data)
                            new_commands.append(pose_cmd)
                        else:
                            new_commands.extend(self._cmd_as_nop(command))
                    else:
                        new_commands.extend(self._cmd_as_nop(command))
                else:
                    new_commands.append(command)
            elif op == self._reward_cmd.cmd():
                if command == self._reward_cmd:
                    new_commands.append(self._reward_replacement.get_cmd())
                else:
                    new_commands.append(command)
            else:
                new_commands.append(command)

        new_event = copy.copy(self._input_event)
        new_event.commands = new_commands
        return new_event

    def _cmd_as_nop(self, command: EventCommand):
        """Returns a set of NOP commands that are the same size as this command."""
        nops = []
        nop = EventCommand([0x1, 0x4, 0xff, 0xff])
        for count in range(int(command.size() / 4)):
            nops.append(nop)
        return nops

    DIALOG_COMMANDS = [0x5, 0x27, 0x6]
    SET_ANI_FRAME_CMD = 0x1F
    SET_POSE_CMD = 0x21

    SET_FLAG_CMD = 0x2d
    GIVE_ITEM_CMD = 0x37

    PC_SPRITE_IDS = (0x20, 0x21, 0x22, 0x23)