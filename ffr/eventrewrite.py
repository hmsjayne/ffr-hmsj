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


class EventRewriter(object):
    def __init__(self, event: Event):
        self._replace_dialog = {}
        self._replace_with_pose = {}

        self._visiting_npcs = []
        self._input_event = event

        self._should_skip_dialog = True

        self._replace_conditional = False
        self._replacement_conditions = []

        self._chest_to_npc = False
        self._chest_change_to_update = []

        self._replace_flag = (-1, -1)
        self._give_item = None

        self._gives_item = False
        for cmd in self._input_event.commands:
            if cmd[0] == 0x37 and cmd[1] == 0x4 and cmd[2] == 0x00:
                self._gives_item = True

    def include_dialogs(self, *string_ids):
        for string_id in string_ids:
            self._replace_dialog[string_id] = string_id

    def visiting_npc(self, *sprite_indices):
        for sprite_index in sprite_indices:
            self._visiting_npcs.append(sprite_index)

    def replace_conditional(self, old_flag: int, new_flag: int):
        self._replace_conditional = True
        self._replacement_conditions.append([old_flag, new_flag])

    def replace_chest(self):
        self._chest_to_npc = True

    def rewrite_dialog(self, original_dialog: int, replacement_dialog: int):
        self._replace_dialog[original_dialog] = replacement_dialog

    def replace_set_frame_with_pose(self, npc_index: int, frame: int, pose: int):
        if npc_index not in self._replace_with_pose:
            self._replace_with_pose[npc_index] = {}
        self._replace_with_pose[npc_index][frame] = pose

    def replace_flag(self, original: int, replacement: int):
        self._replace_flag = (original, replacement)

    def give_item(self, event_item_id: int):
        self._give_item = event_item_id

    def rewrite(self) -> Event:
        new_commands = []
        kept_dialog = []

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
                    kept_dialog.append(self._replace_dialog[str_id])
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
            elif op == 0x36 and self._chest_to_npc:
                #command[0] = 0x2E
                new_commands.append(command)
            elif op == EventRewriter.SET_FLAG_CMD:
                if command.size() == 0x8 and self._replace_conditional:
                    for flags in self._replacement_conditions:
                        if command[2] == flags[0]:
                            command[2] = flags[1]
                elif command.size() == 0x4 and not self._replace_flag == (-1, -1):
                    if command[2] == self._replace_flag[0]:
                        command[2] = self._replace_flag[1]
                new_commands.append(command)
            elif op == EventRewriter.GIVE_ITEM_CMD:
                if command.size() == 4 and command[2] == 0x0:
                    if self._give_item is None:
                        command[0] = EventRewriter.NOP_CMD
                        command[2] = 0xff
                        command[3] = 0xff
                    else:
                        command[3] = self._give_item
                new_commands.append(command)
            else:
                new_commands.append(command)

        for keep_text in self._replace_dialog:
            if self._replace_dialog[keep_text] not in kept_dialog:
                print(f"Warning: Did not see text {hex(keep_text)} in event")

        new_event = copy.copy(self._input_event)
        new_event.commands = new_commands
        return new_event

    def _cmd_as_nop(self, command: EventCommand):
        """Returns a set of NOP commands that are the same size as this command."""

        # This really needs to be done better, but, as a hack, it should work for now?
        nops = []
        nops_required = int(command.size() / 4)
        if self._give_item is not None and not self._gives_item:
            give_cmd = EventCommand([EventRewriter.GIVE_ITEM_CMD, 0x4, 0x0, self._give_item])
            nops.append(give_cmd)

            # Only give it once.
            self._give_item = None

            # Since we used a command, one NOP isn't needed
            nops_required -= 1

        nop = EventCommand([0x1, 0x4, 0xff, 0xff])
        for count in range(nops_required):
            nops.append(nop)
        return nops

    DIALOG_COMMANDS = [0x5, 0x27, 0x6]

    NOP_CMD = 0x1
    SET_ANI_FRAME_CMD = 0x1F
    SET_POSE_CMD = 0x21
    SET_FLAG_CMD = 0x2d
    GIVE_ITEM_CMD = 0x37

    PC_SPRITE_IDS = (0x20, 0x21, 0x22, 0x23)
