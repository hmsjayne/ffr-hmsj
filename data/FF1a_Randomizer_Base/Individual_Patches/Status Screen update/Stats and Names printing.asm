@Modify part of status screen routine to also print MDF and number of hits
@Also uses full words for stats instead of abbreviations
@Replaces part of routine beginning at 0x38FB0
@There, write 0048 0047 XXXXXXXX
@r4 = 0x0
@r5 = contains WRAM pointer for text
@r6 = 0x0802BF81, for printing text
@r7 = don't change!
@r8 = scratch
@r9 = scratch
@r10 = offset of character number

@For text, need [sp] = 0, [sp+4] = 0;
@For numbers, need [sp] = 0, [sp+4] = 3, [sp+8] = 1
.thumb

ldr            r0,[r5]
ldr            r1,StrengthText         @Printing "Strength ..."
str            r4,[sp]                 @Setting params for the text printing
str            r4,[sp,#0x4]
mov            r2,#0x90                @Remember to set all X-coords here...
mov            r3,#0x28
bl             Longcall_6

ldr            r0,[r5]                 @From here, we print every string needed
ldr            r1,AgilityText
mov            r2,#0x90
mov            r3,#0x32
bl             Longcall_6

ldr            r0,[r5]
ldr            r1,IntellectText
mov            r2,#0x90
mov            r3,#0x3C
bl             Longcall_6

ldr            r0,[r5]
ldr            r1,StaminaText
mov            r2,#0x90
mov            r3,#0x46
bl             Longcall_6

ldr            r0,[r5]
ldr            r1,LuckText
mov            r2,#0x90
mov            r3,#0x50
bl             Longcall_6

ldr            r0,[r5]
ldr            r1,AttackText
mov            r2,#0x90
mov            r3,#0x60
bl             Longcall_6

ldr            r0,[r5]
ldr            r1,XText
mov            r2,#0xCE
mov            r3,#0x60
bl             Longcall_6

ldr            r0,[r5]
ldr            r1,AccuracyText
mov            r2,#0x90
mov            r3,#0x6C
bl             Longcall_6

ldr            r0,[r5]
ldr            r1,DefenseText
mov            r2,#0x90
mov            r3,#0x78
bl             Longcall_6

ldr            r0,[r5]
ldr            r1,EvasionText
mov            r2,#0x90
mov            r3,#0x84
bl             Longcall_6

ldr            r0,[r5]
ldr            r1,MDFText
mov            r2,#0x90
mov            r3,#0x90
bl             Longcall_6

@Having printed all text, we proceed to calculating and printing statistics

mov            r1,r10                  @Loading character ID
ldr            r0,[r1]
lsl            r1,r0,#0x3
add            r1,r1,r0
lsl            r1,r1,#0x3
ldr            r2,[sp,#0x24]
ldr            r4,[r2]                 @Loading address of PC data
add            r4,r4,r1                @Now let's save that
mov            r0,r4
ldr            r1,GetFinalStrength     @Base STR, modified by equipment
bl             Longcall_1
mov            r1,r0
ldr            r0,[r5]
mov            r3,#0x3                 @Print up to three digits
str            r3,[sp,#0x4]
mov            r2,#0x1                 @Don't pad with zeroes
str            r2,[sp,#0x8]
mov            r2,#0xD4
mov            r3,#0x28
ldr            r6,PrintNumber
bl             Longcall_6

mov            r0,r4
ldr            r1,GetFinalAgility
bl             Longcall_1
mov            r1,r0
ldr            r0,[r5]
mov            r2,#0xD4
mov            r3,#0x32
bl             Longcall_6

mov            r0,r4
ldr            r1,GetFinalIntellect
bl             Longcall_1
mov            r1,r0
ldr            r0,[r5]
mov            r2,#0xD4
mov            r3,#0x3C
bl             Longcall_6

mov            r0,r4
ldr            r1,GetFinalStamina
bl             Longcall_1
mov            r1,r0
ldr            r0,[r5]
mov            r2,#0xD4
mov            r3,#0x46
bl             Longcall_6

mov            r1,#0x21
ldrb           r1,[r4,r1]              @Loading Luck
ldr            r0,[r5]
mov            r2,#0xD4
mov            r3,#0x50
bl             Longcall_6

mov            r0,r4
ldr            r1,GetAttack
bl             Longcall_1              @Calc Attack stat
mov            r1,r0
ldr            r0,[r5]
mov            r2,#0xD4
mov            r3,#0x60
bl             Longcall_6

mov            r0,r4
ldr            r1,GetAccuracy
bl             Longcall_1
mov            r1,r0
mov            r8,r0
ldr            r0,[r5]
mov            r2,#0xD4
mov            r3,#0x6C
bl             Longcall_6

ldrb           r0,[r4,#0xD]            @For hits determination
mov            r3,r8
lsr            r3,r3,#0x5
add            r3,#0x1                 @Normally (ACC/32) + 1
cmp            r0,#0x2
beq            MonkCalcs
cmp            r0,#0x8                 @Monks and Masters get double hits...
bne            DisplayHits
MonkCalcs:
mov            r0,#0x28
ldrb           r0,[r4,r0]
cmp            r0,#0x0
bne            DisplayHits             @...If they're unarmed
lsl            r3,r3,#0x1
DisplayHits:
mov            r1,r3
ldr            r0,[r5]
mov            r2,#0xBC
mov            r3,#0x60
bl             Longcall_6

mov            r0,r4
ldr            r1,GetDefense
bl             Longcall_1
mov            r1,r0
ldr            r0,[r5]
mov            r2,#0xD4
mov            r3,#0x78
bl             Longcall_6

mov            r0,r4
ldr            r1,GetEvasion
bl             Longcall_1
mov            r1,r0
ldr            r0,[r5]
mov            r2,#0xD4
mov            r3,#0x84
bl             Longcall_6

ldrh           r1,[r4,#0x26]           @Loading Magic Defense
ldr            r0,[r5]
mov            r2,#0xD4
mov            r3,#0x90
bl             Longcall_6

WrapUp:
mov            r0,#0x1
mov            r8,r0
ldr            r1,ReturnAddress
bx             r1

.align 2
GetFinalStrength:
.long 0x08015E75
GetFinalAgility:
.long 0x08015D4D
GetFinalIntellect:
.long 0x08015CB9
GetFinalStamina:
.long 0x08015DE1
GetAttack:
.long 0x0801591D
GetAccuracy:
.long 0x08015F45
GetDefense:
.long 0x080159B5
GetEvasion:
.long 0x08015ACD

PrintNumber:
.long 0x0802C441

ReturnAddress:
.long 0x080392E5

StrengthText:
.long 0x08EE80C0
AgilityText:
.long 0x08EE80D8
IntellectText:
.long 0x08EE80F0
StaminaText:
.long 0x08EE8108
LuckText:
.long 0x08EE8120
AttackText:
.long 0x08EE8138
AccuracyText:
.long 0x08EE8150
DefenseText:
.long 0x08EE8168
EvasionText:
.long 0x08EE8180
MDFText:
.long 0x08EE8198
XText:
.long 0x08EE81AC

Longcall_1:
bx             r1
Longcall_6:
bx             r6
