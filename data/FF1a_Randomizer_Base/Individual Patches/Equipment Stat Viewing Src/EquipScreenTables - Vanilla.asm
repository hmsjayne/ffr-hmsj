@This represents the tables for text/number printing used by the equipment viewing screen
@For use with an unmodified Dawn of Souls ROM
@Copy/paste to $321B0

.thumb
WeaponStatIndexes:
.byte 0x04
.byte 0x05
.byte 0x0F
.byte 0x06

.org 0x08
ArmorStatIndexes:
.byte 0x04
.byte 0x05
.byte 0x06

.org 0x10
WeaponLabelData:
.long 0x081E06BC @ "ATK"
.byte 0x0C
.byte 0x3C
.short 0x0000
.long 0x081E06C4 @ "ACC"
.byte 0x0C
.byte 0x44
.short 0x0000
.long 0x080322D0 @ "CRT"
.byte 0x0C
.byte 0x4C
.short 0x0000
.long 0x081DA5BC @ "EVA"
.byte 0x0C
.byte 0x54
.short 0x0000
.long 0x080322D8 @ "Element:"
.byte 0x98
.byte 0x34
.short 0x0000

.org 0x60
ArmorLabelData:
.long 0x081DA5B4 @ "DEF"
.byte 0x0C
.byte 0x3C
.short 0x0000
.long 0x081E06D4 @ "WGT"
.byte 0x0C
.byte 0x44
.short 0x0000
.long 0x081DA5BC @ "EVA"
.byte 0x0C
.byte 0x4C
.short 0x0000
.long 0x081DC900 @ "Resistance:"
.byte 0x98
.byte 0x34
.short 0x0000

.org 0xB0
SharedLabelPointers:
.long 0x081DA80C @ "STR"
.long 0x081DA828 @ "STA"
.long 0x081DA818 @ "AGL"
.long 0x081DA820 @ "INT"
.long 0x081DA55C @ "HP"
.long 0x081DA568 @ "MP"
.long 0x00000000

.org 0x120
Critical:
.long 0x71826282
.byte 0x82
.byte 0x73
.byte 0x00
.org 0x128
Element:
.long 0x8C826482
.long 0x8D828582
.long 0x8E828582
.long 0x46819482
.byte 0x0

