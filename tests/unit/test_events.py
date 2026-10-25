from doslib.data_source import InMemoryDataSource
from randomizer.events import build_headers, load_event_scripts, parse_script, update_strings
from randomizer.placement import Placement


def test_parse_script_reads_multiple_events():
    source = InMemoryDataSource({
        "scripts/example.script": (
            "begin script=0x10\n"
            "nop\n"
            "begin script=0x20\n"
            "end_event\n"
        )
    })

    events = parse_script("scripts/example.script", source)

    assert events == {
        0x10: "nop\n",
        0x20: "end_event\n",
    }


def test_load_event_scripts_uses_sorted_file_order():
    source = InMemoryDataSource({
        "scripts/b.script": "begin script=0x1\nb\n",
        "scripts/a.script": "begin script=0x1\na\n",
    })

    scripts = load_event_scripts(source)

    assert scripts[0x1] == "b\n"


def test_build_headers_contains_reward_defines():
    headers = build_headers(Placement(), "#define FREE_START set_flag 0x28")

    assert "#define FREE_START set_flag 0x28" in headers
    assert "#define GIVE_KING_REWARD" in headers
    assert "%king_text_id" in headers
    assert "%king_reward_flag" in headers
    assert "%desert_reward_sprite" in headers


def test_update_strings_uses_in_memory_source():
    class FakeEventText:
        strings = {}

    source = InMemoryDataSource({
        "data/TextUpdates.tsv": "0x10\tUpdated text\n",
    })

    update_strings(FakeEventText(), source)

    assert 0x10 in FakeEventText.strings
    assert isinstance(FakeEventText.strings[0x10], bytearray)
