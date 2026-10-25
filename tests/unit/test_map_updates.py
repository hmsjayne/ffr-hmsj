from collections import namedtuple

from randomizer.map_updates import remove_tiles_with_event

Tile = namedtuple("Tile", ["event", "x_pos"])


def test_remove_tiles_with_event_removes_all_matches():
    tiles = [
        Tile(event=0x23D0, x_pos=1),
        Tile(event=0x200C, x_pos=2),
        Tile(event=0x23D0, x_pos=3),
        Tile(event=0x23D0, x_pos=4),
    ]

    remaining = remove_tiles_with_event(tiles, 0x23D0)

    assert [tile.x_pos for tile in remaining] == [2]
