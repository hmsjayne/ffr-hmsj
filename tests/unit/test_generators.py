from doslib.data_source import InMemoryDataSource
from doslib.item import Item
from doslib.spell import SpellData
from randomizer.spellgenerator import SpellGenerator, _grade_to_score as spell_grade_score
from randomizer.treasure import InventoryGenerator, _grade_to_score as item_grade_score


class FakeItems:
    def __init__(self, items):
        self.by_type = [[], items, [], []]

    def all(self):
        return {
            "item": self.by_type[1],
            "weapon": self.by_type[2],
            "armor": self.by_type[3],
        }

    def get_by_type(self, type_name):
        return self.by_type[{"item": 1, "weapon": 2, "armor": 3}[type_name]]


class FakeSpells:
    def __init__(self, spells):
        self.spell_data = spells


def make_item(name, grade):
    item = Item()
    item.id = 1
    item.name = name
    item.item_type = "item"
    item.grade = grade
    item.sort_order = 1
    return item


def test_grade_scores():
    assert item_grade_score("S") == 100
    assert item_grade_score("A+") == 90
    assert item_grade_score("A-") == 80
    assert spell_grade_score("C") == 40


def test_inventory_generator_is_deterministic():
    items = FakeItems([
        make_item("Potion", "S"),
        make_item("Ether", "A"),
        make_item("Antidote", "B"),
        make_item("Tent", "C"),
        make_item("Cottage", "D"),
    ])
    source = InMemoryDataSource({
        "data/ChestData.tsv": "chest_index\ttype\tcontents\tdescription\tmap\tgrade\tnotes\n",
        "data/MapToArea.tsv": "map_index\tname\tarea\n0\tWorld Map\tTest Area\n",
        "data/AreaWeights.tsv": "area\tS\tA\tB\tC\tD\ttotal\nTest Area\t101\t0\t0\t0\t0\t101\n",
    })

    first = InventoryGenerator("seed", items, False, source).get_inventory(0)
    second = InventoryGenerator("seed", items, False, source).get_inventory(0)

    assert first.name == "Potion"
    assert second.name == "Potion"


def test_spell_generator_is_deterministic():
    spell = SpellData()
    spell.spell_index = 3
    spell.name = "Fire"
    spell.school = "black"
    spell.grade = "S"

    first = SpellGenerator("seed", FakeSpells([spell])).get_inventory(0, "black")
    second = SpellGenerator("seed", FakeSpells([spell])).get_inventory(0, "black")

    assert first.spell_index == 3
    assert second.spell_index == 3
