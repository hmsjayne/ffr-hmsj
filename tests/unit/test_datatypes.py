from doslib.classes import JobClass
from doslib.enemy import Encounter, EncounterGroup, EnemyScript, EnemyStats
from doslib.item import Armor, Item, Weapon
from doslib.map import Chest, MapHeader, Npc, Shop, Sprite, Tile
from doslib.spell import SpellData
from stream.inputstream import InputStream
from stream.outputstream import OutputStream


def round_trip(value):
    output = OutputStream()
    value.write(output)
    data = output.get_buffer()
    return type(value)(InputStream(data)), data


def test_npc_round_trip():
    npc = Npc()
    npc.identifier = 2
    npc.event = 0x1F62
    npc.x_pos = 95
    npc.y_pos = 157
    npc.sprite_id = 0xC6
    npc.move_speed = 0
    npc.facing = 3
    npc.in_room = 1

    decoded, _ = round_trip(npc)

    assert vars(decoded) == vars(npc)


def test_item_round_trip():
    item = Item()
    item.sort_order = 0x1234
    item.field_effect = 1
    item.targeting = 2
    item.usage = 3
    item.graphic = 4
    item.power = 0x5678
    item.cost = 0x12345678
    item.sale_price = 0x87654321

    decoded, data = round_trip(item)

    assert len(data) == 16
    for field in ("sort_order", "field_effect", "targeting", "usage", "graphic", "power", "cost", "sale_price"):
        assert getattr(decoded, field) == getattr(item, field)


def test_weapon_and_armor_round_trip():
    weapon = Weapon()
    weapon.sort_order = 1
    weapon.equip_classes = 0x3F
    weapon.atk = 10
    weapon.acc = 20
    weapon.evade = 30
    weapon.spell = 40
    weapon.elements = 0x1234
    weapon.family_effect = 2
    weapon.str_mod = 3
    weapon.sta_mod = 4
    weapon.agi_mod = 5
    weapon.int_mod = 6
    weapon.crit_rate = 7
    weapon.hp_boost = 8
    weapon.mp_boost = 9
    weapon.unused = 10
    weapon.cost = 0x11223344
    weapon.sale_price = 0x55667788

    armor = Armor()
    armor.sort_order = 2
    armor.equip_classes = 0x0F
    armor.defence = 11
    armor.weight = 12
    armor.evade = 13
    armor.spell = 14
    armor.elemental_resists = 0x4321
    armor.str_mod = 15
    armor.sta_mod = 16
    armor.agi_mod = 17
    armor.int_mod = 18
    armor.hp_boost = 19
    armor.mp_boost = 20
    armor.unused = 21
    armor.cost = 0x99AABBCC
    armor.sale_price = 0xDDEEFF00

    decoded_weapon, _ = round_trip(weapon)
    decoded_armor, _ = round_trip(armor)

    assert vars(decoded_weapon)["atk"] == weapon.atk
    assert vars(decoded_weapon)["cost"] == weapon.cost
    assert vars(decoded_armor)["defence"] == armor.defence
    assert vars(decoded_armor)["cost"] == armor.cost


def test_enemy_stats_round_trip():
    enemy = EnemyStats()
    enemy.exp_reward = 10
    enemy.gil_reward = 20
    enemy.max_hp = 30
    enemy.morale = 1
    enemy.unused_ai = 2
    enemy.evasion = 3
    enemy.pdef = 4
    enemy.hit_count = 5
    enemy.acc = 6
    enemy.atk = 7
    enemy.agi = 8
    enemy.intel = 9
    enemy.crit_rate = 10
    enemy.status_atk_elem = 0x1234
    enemy.status_atk_ailment = 11
    enemy.family = 12
    enemy.mdef = 13
    enemy.unused = 14
    enemy.elem_weakness = 0x5678
    enemy.elem_resists = 0x9ABC
    enemy.drop_type = 15
    enemy.drop_id = 16
    enemy.drop_chance = 17
    enemy.padding = [18, 19, 20]

    decoded, _ = round_trip(enemy)

    assert vars(decoded) == vars(enemy)


def test_spell_data_round_trip():
    spell = SpellData()
    spell.usage = 1
    spell.target = 2
    spell.power = 0x1234
    spell.elements = 0x5678
    spell.type = 3
    spell.graphic_index = 4
    spell.accuracy = 5
    spell.level = 6
    spell.mp_cost = 7
    spell.price = 0x89ABCDEF

    decoded, _ = round_trip(spell)

    assert vars(decoded)["usage"] == spell.usage
    assert vars(decoded)["price"] == spell.price


def test_job_class_round_trip():
    job = JobClass()
    job.base_hp = 0x1234
    job.base_mp = 0x5678
    job.starting_spell_level = 1
    job.base_strength = 2
    job.base_agility = 3
    job.base_intellect = 4
    job.base_stamina = 5
    job.base_luck = 6
    job.base_accuracy = 7
    job.base_evade = 8
    job.base_mdef = 9
    job.weapon_id = 10
    job.armor_id = 11
    job.unused = 12

    decoded, _ = round_trip(job)

    assert vars(decoded) == vars(job)


def test_encounter_round_trip():
    encounter = Encounter()
    encounter.config = 2
    encounter.unrunnable = 1
    encounter.surprise_chance = 0x1234
    encounter.groups = []
    for index in range(4):
        group = EncounterGroup()
        group.enemy_id = index
        group.min_count = index + 1
        group.max_count = index + 2
        group.unused = index + 3
        encounter.groups.append(group)

    decoded, _ = round_trip(encounter)

    assert decoded.config == encounter.config
    assert decoded.surprise_chance == encounter.surprise_chance
    assert [vars(group) for group in decoded.groups] == [vars(group) for group in encounter.groups]


def test_map_entity_round_trips():
    for value in (Chest(), MapHeader(), Shop(), Sprite(), Tile()):
        if isinstance(value, MapHeader):
            value.low_x, value.low_y, value.high_x, value.high_y = 1, 2, 3, 4
        else:
            value.identifier = 2
            value.x_pos = 3
            value.y_pos = 4

        decoded, _ = round_trip(value)
        assert vars(decoded) == vars(value)


def test_enemy_script_round_trip():
    script = EnemyScript()
    script.spell_chance = 1
    script.ability_chance = 2
    script.spells = [3, 4, 5, 6, 7, 8, 9, 10]
    script.spell_null = 11
    script.abilities = [12, 13, 14, 15]
    script.ability_null = 16

    decoded, _ = round_trip(script)

    assert vars(decoded) == vars(script)
