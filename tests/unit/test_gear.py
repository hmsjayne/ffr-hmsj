from types import SimpleNamespace

from randomizer.gear import randomize_starting_gear
from randomizer.rng import RNG


class FakeItems:
    def __init__(self, weapons, armors):
        self.weapons = weapons
        self.armors = armors

    def get_by_type(self, type_name):
        return self.weapons if type_name == "weapon" else self.armors


def test_randomize_starting_gear_assigns_usable_gear():
    weapon = SimpleNamespace(id=1, equip_classes=0x3F)
    armor = SimpleNamespace(id=1, equip_classes=0x3F)
    classes = [SimpleNamespace(weapon_id=0, armor_id=0) for _ in range(6)]

    randomize_starting_gear(RNG(1), FakeItems([weapon], [armor]), classes)

    assert all(job.weapon_id == 1 for job in classes)
    assert all(job.armor_id == 1 for job in classes)


def test_randomize_starting_gear_filters_unusable_and_high_level_gear():
    usable_weapon = SimpleNamespace(id=1, equip_classes=0x01)
    unusable_weapon = SimpleNamespace(id=2, equip_classes=0)
    dummy_weapon = SimpleNamespace(id=0, equip_classes=0x3F)
    usable_armor = SimpleNamespace(id=1, equip_classes=0x01)
    unusable_armor = SimpleNamespace(id=2, equip_classes=0)
    high_armor = SimpleNamespace(id=0x1C, equip_classes=0x3F)
    classes = [SimpleNamespace(weapon_id=0, armor_id=0)]

    randomize_starting_gear(
        RNG(1),
        FakeItems([usable_weapon, unusable_weapon, dummy_weapon],
                  [usable_armor, unusable_armor, high_armor]),
        classes,
    )

    assert classes[0].weapon_id == 1
    assert classes[0].armor_id == 1
