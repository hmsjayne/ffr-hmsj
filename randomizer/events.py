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

from doslib.event import EventTables, EventTextBlock
from doslib.rom import Rom
from doslib.textblock import TextBlock
from event.easm import parse, link
from event.epp import pparse


def build_headers(placements, start_cmds: str) -> str:
    header = f"""
    ; Standard defines
    #define WINDOW_TOP 0x0
    #define WINDOW_BOTTOM 0x1
    #define DIALOG_WAIT 0x1
    #define DIALOG_AUTO_CLOSE 0x0
    
    {start_cmds}
    
    ; Reward definitions
    """

    text_ids = ""
    flag_names = ""
    for placement in placements.all_placements():
        flag = f"\tset_flag {hex(placement.plot_flag)}\\\n" if placement.plot_flag is not None else ""
        item = f"\tgive_item {hex(placement.plot_item)}\\\n" if placement.plot_item is not None else ""
        extra = f"\t{placement.extra}\n" if placement.extra is not None else ""
        header += f"#define GIVE_{placement.source.upper()}_REWARD \\\n{flag}{item}{extra}\n"
        text_ids += f"%{placement.source.lower()}_text_id {hex(placement.reward_text_id)}\n"
        flag_names += f"%{placement.source.lower()}_reward_flag {hex(placement.plot_flag)}\n"

        # One special case for "flags" -- note the sprite for the desert location
        if placement.source == "desert":
            flag_names += f"%desert_reward_sprite {hex(placement.sprite)}\n"

    header += f"\n;String ID references\n{text_ids}\n\n;Plot flags\n{flag_names}\n\n"
    return header


def parse_script(script: str, data_source=None) -> dict:
    events = {}
    script_id = None
    script_code = ""
    if data_source is None:
        from doslib.data_source import FileSystemDataSource

        data_source = FileSystemDataSource()
    for line in data_source.read_text(script).splitlines(keepends=True):
        if line.startswith("begin script="):
            if script_id is not None:
                events[script_id] = script_code
                script_code = ""
            script_id = int(line[line.find("=") + 1:], 0)
        elif script_id is not None:
            script_code += line
    if script_id is not None:
        events[script_id] = script_code
    return events


def load_event_scripts(data_source=None) -> dict:
    if data_source is None:
        from doslib.data_source import FileSystemDataSource

        data_source = FileSystemDataSource()
    scripts = {}
    for file in data_source.list_files("scripts", ".script"):
        add_events = parse_script(f"scripts/{file}", data_source)
        for event_id, source in add_events.items():
            scripts[event_id] = source
    return scripts


def compile_event_scripts(rom: Rom, placement, free_header: str, event_scripts: dict):
    """Compile all event scripts and return the data/table patch dictionaries."""
    headers = build_headers(placement, free_header)
    event_tables = EventTables(rom)
    event_script_patches = {}
    for event_id in sorted(event_scripts.keys()):
        script = event_scripts[event_id]
        preprocess = pparse(f"{headers}\n\n{script}")
        event_icode = parse(preprocess)

        event_addr = event_tables.get_addr(event_id)
        vanilla_size = rom.get_event_size(event_addr)

        # If the event doesn't fit in the vanilla location, move it to part of our free space.
        if event_icode.size > vanilla_size:
            event_addr = rom.get_free_space(f"event_{hex(event_id)}", event_icode.size)

        event_script_patches[Rom.pointer_to_offset(event_addr)] = link(event_icode, event_addr)
        event_tables.set_addr(event_id, event_addr)

    return event_script_patches, event_tables.get_patches()


def update_strings(event_text: EventTextBlock, data_source=None):
    if data_source is None:
        from doslib.data_source import FileSystemDataSource

        data_source = FileSystemDataSource()
    for line in data_source.read_text("data/TextUpdates.tsv").splitlines():
        string_num, text = line.strip().split('\t')
        string_num = int(string_num, 16)

        if not text.endswith('\x00'):
            text += '\x00'

        event_text.strings[string_num] = TextBlock.encode_text(text)
