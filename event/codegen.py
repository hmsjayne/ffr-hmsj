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

from event.tokens import Uint16


def end_event(parameters: list) -> list:
    return [0x0, 0x4, 0xff, 0xff]


def load_text(parameters: list) -> list:
    where = parameters[0]
    dialog_id = Uint16(parameters[1])
    bytecode = [0x05, 0x8]
    bytecode.extend(dialog_id.bytes())
    bytecode.extend([where, 0xff, 0xff, 0xff])
    return bytecode


def close_dialog(parameters: list) -> list:
    when = parameters[0]
    return [0x6, 0x4, when, 0xff]


def jump(parameters: list) -> list:
    label = parameters[0]
    return [0xc, 0x8, 0xff, 0xff, label]


def jump_chest_empty(parameters: list) -> list:
    label = parameters[0]
    return [0xd, 0xc, 0x0, 0xff, label, 0x0, 0x0, 0x0, 0x0]


def music(parameters: list) -> list:
    mode = parameters[0]
    sound_id = Uint16(parameters[1])
    bytecode = [0x11, 0x8, mode, 0xff]
    bytecode.extend(sound_id.bytes())
    bytecode.extend([0xff, 0xff])
    return bytecode


def set_repeat(parameters: list) -> list:
    times = parameters[0]
    return [0x19, 0x4, 0x0, times]


def repeat(parameters: list) -> list:
    step = parameters[0]
    label = parameters[1]
    return [0x19, 0x8, step, 0xff, label]


def show_dialog(parameters: list) -> list:
    return [0x27, 0x4, 0x0, 0xff]


def set_flag(parameters: list) -> list:
    flag = parameters[0]
    return [0x2d, 0x4, flag, 0x0]


def check_flag(parameters: list) -> list:
    flag = parameters[0]
    cond = parameters[1]
    label = parameters[2]
    return [0x2d, 0x8, flag, cond, label]


def remove_trigger(parameters: list) -> list:
    trigger_id = Uint16(parameters[0])
    bytecode = [0x2e, 0x4]
    bytecode.extend(trigger_id.bytes())
    return bytecode


def npc_update(parameters: list) -> list:
    action = parameters[0]
    npc_id = parameters[1]
    return [0x30, 0x4, action, npc_id]


def set_npc_event(parameters: list) -> list:
    npc_id = parameters[0]
    event_id = Uint16(parameters[1])
    bytecode = [0x30, 0x8, 0x1, npc_id]
    bytecode.extend(event_id.bytes())
    bytecode.extend([0xff, 0xff])
    return bytecode


def remove_all(parameters: list) -> list:
    trigger_id = Uint16(parameters[0])
    bytecode = [0x36, 0x4]
    bytecode.extend(trigger_id.bytes())
    return bytecode


def give_item(parameters: list) -> list:
    item = parameters[0]
    return [0x37, 0x4, 0x0, item]


def take_item(parameters: list) -> list:
    item = parameters[0]
    return [0x37, 0x4, 0x1, item]


def check_item(parameters: list) -> list:
    item = parameters[0]
    label = parameters[1]
    return [0x37, 0x4, 0x2, item, label]


def jump_by_dir(parameters: list) -> list:
    up_label = parameters[0]
    right_label = parameters[1]
    left_label = parameters[2]
    return [0x42, 0x10, 0xff, 0xff, up_label, right_label, left_label]
