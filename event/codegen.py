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
from evtasm import Uint16


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
    bytecode = [0xd, 0xc, 0x0, 0xff, label]
    bytecode.extend([0x0, 0x0, 0x0, 0x0])
    return bytecode


def music(parameters: list) -> list:
    mode = parameters[0]
    sound_id = Uint16(parameters[1])
    bytecode = [0x11, 0x8, mode, 0xff]
    bytecode.extend(sound_id.bytes())
    bytecode.extend([0xff, 0xff])
    return bytecode


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