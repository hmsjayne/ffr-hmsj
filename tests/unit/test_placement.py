from doslib.item import Item
from randomizer.placement import Placement
from randomizer.placement_solver import PlacementPair


def test_placement_data_is_loaded():
    placements = Placement().all_placements()

    assert len(placements) == 27
    assert placements[0].source == "king"
    assert placements[0].reward == "bridge"
    assert placements[0].map_id == 0x39
    assert len({placement.source for placement in placements}) == len(placements)


def test_update_gear_replaces_reward_and_allocates_free_flag():
    placement = Placement()

    gear = Item()
    gear.item_type = "weapon"
    gear.id = 7
    gear.name = "Test Sword"

    placement.update_gear("bridge", gear)
    updated = next(item for item in placement.all_placements() if item.source == "king")

    assert updated.reward == "free_bridge"
    assert updated.plot_flag == 0x28
    assert updated.plot_item is None
    assert updated.extra == "give_item_ex 0x2 0x7"


def test_update_placements_moves_reward_to_source():
    placement = Placement()
    placement.update_placements((
        PlacementPair(item="lute", location="king"),
        PlacementPair(item="bridge", location="sara"),
    ))

    placements = placement.all_placements()

    assert placements[0].source == "king"
    assert placements[0].reward == "lute"
    assert placements[1].source == "sara"
    assert placements[1].reward == "bridge"


def test_update_placements_skips_caravan():
    placement = Placement()
    placement.update_placements((
        PlacementPair(item="bottle", location="caravan"),
        PlacementPair(item="lute", location="king"),
    ))

    placements = placement.all_placements()

    assert len(placements) == 1
    assert placements[0].source == "king"


def test_placement_details_are_namedtuples():
    placement = Placement().all_placements()[0]

    assert placement._asdict()["source"] == "king"
    assert placement._asdict()["reward"] == "bridge"
