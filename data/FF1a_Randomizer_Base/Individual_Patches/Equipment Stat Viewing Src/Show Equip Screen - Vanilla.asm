@This here is the relevant part of the item menu routine that needs to be modified
@Will go in its own region to avoid pain
@Link from 0x32160: 004A 1047 XXXXXXXX, where the X's form a pointer to free space

@Idea: for gear stats, allow definitions to specify whether positive values appear in green?
.thumb

mov				r2,#0x0				@Setting up the window that will hold the gear stats
mov				r0,#0x10
lsl				r0,r0,#0x8
add				r0,#0x1E
lsl				r0,r0,#0x10			@Will be 0x10 high, 0x1E wide
str     		r0,[sp,#0x24]
ldr     		r0,[r5]
add     		r1,sp,#0x24
str     		r1,[sp]
str     		r2,[sp,#0x4]
mov     		r1,#0x3				@Will be offset 0x0 horizontally, 0x3 vertically
str     		r1,[sp,#0x8]
mov     		r2,#0x4				@Use window style 0x4
ldr     		r4,DrawWindow		@Now make the window!
bl      		Longcall_4
mov     		r7,#0x0
mov     		r1,r10
add     		r1,#0xC
str     		r1,[sp,#0x34]
ldr				r4,Bmem56E8
add				r4,r10
mov				r3,r13
add				r3,#0x10
str				r3,[sp,#0x44]		@Setting up some params...
ldr				r5,VRAMPtr
str				r5,[sp,#0x3C]
mov				r6,#0x90
lsl				r6,r6,#0xE
str				r6,[sp,#0x40]
@---REMOVED PC SPRITE/NAME PRINTING---
@---REGISTER r9 IS FREE---
@---[sp+$3C],[sp+$40] ARE FREE---
ldr     		r0,CursorPosPointer	@Now get selected item's inventory position
add     		r0,r10
ldr     		r0,[r0]
mov     		r4,#0x4
ldsh    		r1,[r0,r4]
ldrb    		r0,[r0,#0x7]
lsl     		r0,r0,#0x18
asr     		r0,r0,#0x18
lsl     		r0,r0,#0x1
add     		r1,r1,r0
ldr     		r5,Bmem56F0
add     		r5,r10
mov     		r8,r5
ldr     		r0,[r5]				@r0 = BattleMem+$56F0
mov				r3,#0x20
lsl				r3,r3,#0x14
add				r3,#0x10			@0x02000010 = text pointer table pointers for items/weapon/armor
ldr     		r6,InventoryPointer
add     		r6,r10
ldr     		r2,[r6]
lsl     		r5,r1,#0x2
add     		r2,r2,r5
ldrb    		r1,[r2]				@Get selected item's item type
lsl     		r1,r1,#0x2
add     		r1,r1,r3			@Get right pointer table...
ldrb    		r2,[r2,#0x1]		@Get selected's sub-ID
ldr     		r3,[r1]
lsl     		r1,r2,#0x1
add     		r1,r1,r2
lsl     		r1,r1,#0x2
add     		r1,r1,r3			@Go to item's entry in pointer table
ldr     		r1,[r1]
mov     		r4,#0x0
str     		r4,[sp]
str     		r4,[sp,#0x4]
mov     		r2,#0x8
mov     		r3,#0x20
ldr     		r4,PrintText		@So, print selected item's name
bl      		Longcall_4
@---REMOVED ITEM QUANTITY PRINTING----
@---REGISTERS r8, r9 ARE FREE---
ldr				r0,[r6]
add				r1,r0,r5
ldrb			r0,[r1]				@
str				r0,[sp,#0x3C]		@Store item type to stack
cmp				r0,#0x2				@Check if it's a weapon or armor
beq				Weapon
Armor:
ldr				r2,ArmorDataTable
b				GearSpellPrinting
Weapon:
ldr				r2,WeaponDataTable
GearSpellPrinting:					@Print the spell cast by this equipment, if it has one
ldrb    		r1,[r1,#0x1]
lsl     		r0,r1,#0x3
sub     		r0,r0,r1
lsl     		r0,r0,#0x2
add     		r5,r0,r2			@Advance to gear's entry in the table
str				r5,[sp,#0x40]		@And store to the stack
ldrb			r0,[r5,#0x7]		@Load spell this gear casts
cmp				r0,#0x00
beq				ClassNamePrinting
cmp				r0,#0xFF
beq				ClassNamePrinting	@If this gear doesn't cast anything, don't print anything
ldr				r1,SpellNamePointers
lsl				r0,r0,#0x3
ldr				r1,[r1,r0]			@Load spell name text
mov				r0,r8				@Mem pointer used for text printing
ldr				r0,[r0]
mov				r2,#0x0
str				r2,[sp]
str				r2,[sp,#0x4]
mov				r2,#0x86
mov				r3,#0x20
bl				Longcall_4			@Print spell's name text!
ClassNamePrinting:
ldrh    		r0,[r5,#0x2]		@Load weapon's equip halfword
str     		r0,[sp,#0x30]
mov     		r5,#0x0				@Now, for every class check if they can equip this
ClassColumnLoop:
mov     		r7,#0x0				@r5 = column count, r7 = row count in a column
lsl     		r3,r5,#0x1
mov     		r9,r3
add     		r4,r5,#0x1
str     		r4,[sp,#0x38]
lsl     		r0,r5,#0x13
mov     		r6,#0xF8
lsl     		r6,r6,#0xF			@0x7C = base Y-coord of class names
add     		r6,r6,r0
mov     		r8,r6
ClassRowLoop:
mov     		r1,r9
add     		r0,r1,r5
add     		r0,r0,r7
lsl     		r0,r0,#0x10
lsr     		r6,r0,#0x10
ldr     		r2,TakeRemainder
mov     		r0,r6
mov     		r1,#0x6
bl      		Longcall_2
mov     		r4,r0
lsl     		r4,r4,#0x10
lsr     		r4,r4,#0x10
ldr     		r2,Divide
mov     		r0,r6
mov     		r1,#0x6
bl      		Longcall_2
lsl     		r0,r0,#0x10
lsr     		r0,r0,#0xD
add     		r4,r4,r0
mov     		r0,#0x1
lsl     		r0,r4
mov				r3,#0x0
str				r3,[sp,#0x4]
mov				r4,#0x0
lsl     		r0,r0,#0x10
lsr     		r3,r0,#0x10
ldr     		r2,[sp,#0x30]
and     		r3,r2				@Yes, all that is in service to checking a bit...
cmp     		r3,#0x0
bne     		CanEquip
mov				r4,#0x1				@If the class can't equip, text will be gray
CanEquip:
ldr     		r0,Bmem56F0
add     		r0,r10
ldr     		r0,[r0]
lsl     		r1,r6,#0x2
ldr     		r3,ClassNamePointers
add     		r1,r1,r3
ldr     		r1,[r1]
mov     		r2,#0x4C
mul     		r2,r7
add     		r2,#0x8
lsl     		r2,r2,#0x10
lsr     		r2,r2,#0x10
str     		r4,[sp]				@Store white or gray colour, as needed
mov     		r4,r8
lsr     		r3,r4,#0x10
ldr     		r4,PrintText
bl      		Longcall_4
add     		r7,#0x1
cmp     		r7,#0x2
bgt     		ClassColumnCheck
b       		ClassRowLoop
ClassColumnCheck:
ldr     		r5,[sp,#0x38]
cmp     		r5,#0x3
bgt     		ElementsHandling	@If we've gone through all classes, move on
b       		ClassColumnLoop
ElementsHandling:
@Now handle elemental properties?
ldr				r5,[sp,#0x40]		@Get entry again
ldrh			r2,[r5,#0x8]		@Load element data
mov				r1,#0x0
mov				r3,r0
ldr				r4,ReorderElements	@Re-order element bits for printing
bl				Longcall_4
mov				r1,r0
ldr				r7,Bmem56F0
add				r7,r7,r10
ldr				r0,[r7]				@Load pointer for text printing
mov				r2,#0x23
lsl				r2,r2,#0x5
add				r2,#0x4
sub				r0,r0,r2			@Subtract 0x464 so it works with the vanilla routine
mov				r2,#0x84
mov				r3,#0x3C			@Set base coords
ldr				r4,DisplayElements
bl				Longcall_4			@Display the list of elements
@The label for the list will come later
StatModsHandling:
ldr				r4,PrintNumbers
mov				r6,#0x0				@Initialize loop counter
mov				r2,#0x3
str				r2,[sp,#0x4]		@Numbers are right-aligned
mov				r2,#0x1
str				r2,[sp,#0x8]		@Don't add leading zeros
add				r5,#0x0A			@In piece's data, advance to STR mod for armor
AdvanceToMods:
add				r5,#0x01			@And add one more...you'll see why later
ldr				r0,[sp,#0x3C]		@Load equip's item type
sub				r0,#0x2				@Now armor = 0x1, weapon = 0x0
sub				r5,r5,r0			@If it's an armor, undo that last addition
StatModLoop:
ldsb			r1,[r5,r6]
mov				r2,#0x0
mov				r0,r1
beq				PrintStatMod		@Default colour is white
bpl				StatPositive
StatNegative:
mov				r2,#0x1				@If stat mod is negative colour is gray
neg				r1,r1				@Also flip number's sign for printing
b				PrintStatMod
StatPositive:
mov				r2,#0x3				@Positive mod gives green
PrintStatMod:
str				r2,[sp]
ldr				r0,[r7]
mov				r2,#0x58
lsl				r3,r6,#0x3			@Y-coord = loop counter*8 + 0x3C
add				r3,#0x3C
bl				Longcall_4			@So, print the number
add				r6,#0x1
cmp				r6,#0x4
beq				AdvanceToMods		@HP/MP mods need further adjustment for weapon/armor offset differences
cmp				r6,#0x5
ble				StatModLoop
GearStatsHandling:
mov				r0,#0x0
str				r0,[sp,#0x0]		@To start, gear stats will be printed in white
ldr				r0,[sp,#0x3C]
cmp				r0,#0x3
beq				ArmorStats
WeaponStats:
ldr				r1,WeaponStatsIndexes	@We're loading a list of which stats to print out
b				StatsContinue
ArmorStats:
ldr				r1,ArmorStatsIndexes
StatsContinue:
mov				r8,r1
ldr				r5,[sp,#0x40]		@Load gear data...
mov				r6,#0x0
StatsPrintLoop:
mov				r3,r8
ldrb			r2,[r3,r6]			@Load index of stat to load from piece's data
cmp				r2,#0x0
ble				StatsLabelsHandling	@If index is zero or negative, we've reached the end
ldrb			r1,[r5,r2]			@Load the stat
mov				r2,#0x0
cmp				r6,#0x2
ble				PrintStatValue		@The first three stats can't be negative in any case, so don't check
lsl				r1,r1,#0x18
asr				r1,r1,#0x18			@Convert to signed byte
bpl				CheckHits			@If positive or zero, check if positive gets green scheme (TEMP)
mov				r2,#0x1				@Else, set colour to gray
neg				r1,r1				@And get the negative value of the stat
b				PrintStatValue
CheckHits:
ldrb			r3,[r3,r6]
cmp				r3,#0x12
bne				PrintStatValue
cmp				r1,#0x1
blt				PrintStatValue
mov				r2,#0x3				@If this is Hits we're displaying and it's >0, show in green
PrintStatValue:
str				r2,[sp]
mov				r2,#0x24			@TEMP?
lsl				r3,r6,#0x3
add				r3,#0x3C
ldr				r0,[r7]				@Retrieve the WRAM pointer
bl				Longcall_4
add				r6,#0x1
cmp				r6,#0x7
ble				StatsPrintLoop		@Cap it at 8 values printed...just in case
StatsLabelsHandling:
mov				r0,#0x0
str				r0,[sp]
str				r0,[sp,#0x4]
str				r0,[sp,#0x8]		@Clear out all of the flags
ldr				r4,PrintText
ldr				r0,[sp,#0x3C]		@Once more loading the item type
cmp				r0,#0x2
bne				ArmorTexts
WeaponTexts:
ldr				r3,WeaponTextPointers
b				TextsContinue
ArmorTexts:
ldr				r3,ArmorTextPointers
TextsContinue:
mov				r8,r3
mov				r6,#0x0
StatsLabelsPrintLoop:
lsl				r5,r6,#0x3			@Each text entry has eight bytes - four bytes for text pointer, two coords, two padding
add				r5,r8
ldr				r0,[r7]
ldr				r1,[r5]				@Load text pointer for this stat label
cmp				r1,#0x0
ble				SharedLabels		@If no text pointer, we've reached the end of the list - exit
ldrb			r2,[r5,#0x4]
ldrb			r3,[r5,#0x5]		@Load coords to place text at
bl				Longcall_4
add				r6,#0x1
cmp				r6,#0x7
ble				StatsLabelsPrintLoop		@Only up to 8 labels allowed
SharedLabels:
@Now for shared labels, for the attribute mods
mov				r6,#0x0
ldr				r5,SharedTextPointers
SharedLabelsLoop:
lsl				r1,r6,#0x2
ldr				r1,[r5,r1]			@Advance to text pointer
cmp				r1,#0x0
ble				End
ldr				r0,[r7]				@Get the WRAM pointer one last time
mov				r2,#0x40			@TEMP
lsl				r3,r6,#0x3
add				r3,#0x3C
bl				Longcall_4			@Print the label
add				r6,#0x1
cmp				r6,#0x6				@Max of 6 shared labels, for now
blt				SharedLabelsLoop
End:
ldr				r5,EndAddress
bx				r5					@back to the normal routine

.align 2
Longcall_2:
bx			r2
Longcall_4:
bx			r4

Bmem56E8:
.long 0x000056E8
Bmem56F0:
.long 0x000056F0
InventoryPointer:
.long 0x00005718
CursorPosPointer:
.long 0x0000802C
VRAMPtr:
.long 0x06017800


Divide:
.long 0x08000F19
TakeRemainder:
.long 0x08000F2D
DrawWindow:
.long 0x0802BE41
PrintText:
.long 0x0802BF81
PrintNumbers:
.long 0x0802C441
ReorderElements:
.long 0x08041325
DisplayElements:
.long 0x0804142D
WeaponDataTable:
.long 0x0819F33C
ArmorDataTable:
.long 0x0819FA58
SpellNamePointers:
.long 0x081A1650
ClassNamePointers:
.long 0x081DA938
WeaponStatsIndexes:
.long 0x080321B0
ArmorStatsIndexes:
.long 0x080321B8
WeaponTextPointers:
.long 0x080321C0
ArmorTextPointers:
.long 0x08032210
SharedTextPointers:
.long 0x08032260

EndAddress:
.long 0x08032525
