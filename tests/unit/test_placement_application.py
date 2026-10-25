from types import SimpleNamespace

from randomizer.placement_application import apply_placements


class FakePlacement:
    def __init__(self, placements):
        self.placements = placements

    def all_placements(self):
        return self.placements


class FakeMap:
    def __init__(self, npcs=None, chests=None, sprites=None):
        self.npcs = npcs or []
        self.chests = chests or []
        self.sprites = sprites or []

    def get_event_chest(self, chest_id):
        return self.chests[chest_id], self.sprites[chest_id]

    def find_npc(self, sprite):
        for index, npc in enumerate(self.npcs):
            if npc.sprite_id == sprite:
                return index
        raise RuntimeError("not found")


class FakeMaps:
    def __init__(self, maps):
        self.maps = maps

    def get_map(self, map_id):
        return self.maps[map_id]


def placement(**overrides):
    values = {
        "source": "king",
        "type": "npc",
        "sprite": 0x22,
        "movable": True,
        "map_id": 0x39,
        "index": 0,
        "ship_x": 1,
        "ship_y": 2,
        "airship_x": 3,
        "airship_y": 4,
        "reward": "bridge",
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def test_apply_npc_placement_and_vehicle_starts():
    npc = SimpleNamespace(sprite_id=0, move_speed=10)
    maps = FakeMaps({0x39: FakeMap(npcs=[npc])})
    starts = {
        "ship": SimpleNamespace(x=0, y=0),
        "airship": SimpleNamespace(x=0, y=0),
    }

    apply_placements(
        FakePlacement([placement(reward="airship", movable=False)]),
        maps,
        starts,
    )

    assert npc.sprite_id == 0x22
    assert npc.move_speed == 0
    assert starts["airship"].x == 3
    assert starts["airship"].y == 4


def test_apply_chest_placement_replaces_chest_with_npc():
    chest = object()
    sprite = SimpleNamespace(x_pos=10, y_pos=20, event=0x1234)
    chest_map = FakeMap(chests=[chest], sprites=[sprite])
    maps = FakeMaps({0x5B: chest_map})
    starts = {
        "ship": SimpleNamespace(x=0, y=0),
        "airship": SimpleNamespace(x=0, y=0),
    }

    apply_placements(
        FakePlacement([placement(type="chest", map_id=0x5B, index=0, sprite=0x94)]),
        maps,
        starts,
    )

    assert chest_map.chests == []
    assert chest_map.sprites == []
    assert len(chest_map.npcs) == 1
    new_npc = chest_map.npcs[0]
    assert new_npc.identifier == 0x2
    assert new_npc.x_pos == 10
    assert new_npc.y_pos == 20
    assert new_npc.event == 0x1234
    assert new_npc.sprite_id == 0xC7


def test_apply_unknown_placement_type_fails_clearly():
    maps = FakeMaps({0x39: FakeMap()})
    starts = {}

    try:
        apply_placements(FakePlacement([placement(type="mystery")]), maps, starts)
    except RuntimeError as exc:
        assert "Unknown placement type" in str(exc)
    else:
        raise AssertionError("Expected RuntimeError")
