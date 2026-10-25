from doslib.maps import ItemChest, MoneyChest, TreasureChest
from doslib.rom import Rom
from randomizer.game_data import VehiclePosition, load_vehicle_starts, pack_chests, pack_vehicle_starts
from stream.inputstream import InputStream


def test_vehicle_starts_round_trip():
    rom_data = bytearray(0x65278 + 16)
    starts = {
        "ship": VehiclePosition(x=0x11223344, y=0x55667788),
        "airship": VehiclePosition(x=0x99AABBCC, y=0xDDEEFF00),
    }
    patch = pack_vehicle_starts(starts)
    rom_data[0x65278:0x65278 + 16] = patch[0x65278]

    decoded = load_vehicle_starts(Rom(rom_data))

    assert decoded == starts


def test_pack_chests():
    item_chest = ItemChest(0x80000000)
    item_chest.item_type = 2
    item_chest.item_id = 0x1234
    item_chest.id = 0x96
    money_chest = MoneyChest(0)
    money_chest.qty = 0xABCDEF
    money_chest.id = 7

    patch = pack_chests([item_chest, money_chest])
    data = patch[0x217FB4]

    stream = InputStream(data)
    decoded_item = TreasureChest.read(stream)
    decoded_money = TreasureChest.read(stream)

    assert isinstance(decoded_item, ItemChest)
    assert decoded_item.item_type == item_chest.item_type
    assert decoded_item.item_id == item_chest.item_id
    assert decoded_item.id == item_chest.id
    assert isinstance(decoded_money, MoneyChest)
    assert decoded_money.qty == money_chest.qty
    assert decoded_money.id == money_chest.id
