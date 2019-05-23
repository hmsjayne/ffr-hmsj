@Rewriting the item give/take/check command to allow for immediate parameters
@by setting bit 0x40 in the mode parameter
@However, you must use the 12-length command!
@For 0x5E318

.thumb

push           {r4-r7,r14}
mov            r7,r10
mov            r6,r9
mov            r5,r8
push           {r5-r7}
mov            r10,r0
ldr            r4,GetVarMem
bl             Longcall_4
mov            r8,r0
ldr            r0,EventStructPointer
add            r0,r10
ldr            r0,[r0]
ldr            r0,[r0]
mov            r9,r0                   @Address of command in ROM
mov            r3,r9                   @Copy to r3
ldrb           r1,[r0,#0x2]            @Loading command's mode byte
mov            r0,#0x40
and            r0,r1
beq            CheckTradeFlag
ldrb           r6,[r3,#0x8]            @Load item type
ldrb           r7,[r3,#0xA]            @And item ID
b              CommandSort             @Merge with other branches now

CheckTradeFlag:
mov            r0,#0x80                @Are we looking for a dwarf trade quest item?
and            r0,r1
cmp            r0,#0x0
bne            TradeQuestSelection
ldrb           r1,[r3,#0x3]            @If not, load event item index from command
b              LoadItemFromTable

TradeQuestSelection:                   @If so, advance to the input for our permutation of the quest
ldr            r1,TradeQuestSelectionParams
ldr            r0,TradeQuestCounter
add            r0,r8
ldrb           r0,[r0]
lsl            r0,r0,#0x2
ldrb           r2,[r3,#0x3]            @Loading quest index from command
add            r0,r0,r2
add            r1,#0x2
add            r0,r0,r1
ldrb           r1,[r0]                 @Use that to get the event item index

LoadItemFromTable:
ldr            r0,EventItemList
lsl            r1,r1,#0x1              @Multiply input by 2...
ldrb           r6,[r0,r1]              @Load item type
add            r0,#0x1
ldrb           r7,[r0,r1]              @And item ID
CommandSort:
ldrb           r0,[r3,#0x2]            @Reload command mode byte
mov            r1,#0x3F                @Strip flags from mode byte
and            r1,r0
cmp            r1,#0x1                 @Are we adding, removing or checking for an item?
beq            RemoveItem
cmp            r1,#0x1
bgt            CommandSort_2
cmp            r1,#0x0
beq            AddItem
b              MoveToNextEvent

CommandSort_2:
cmp            r1,#0x2
beq            CheckForItem
b              MoveToNextEvent
AddItem:
mov            r0,r8
mov            r1,r6
mov            r2,r7
mov            r3,#0x1
ldr            r4,AddItemToInventory
bl             Longcall_4
ldr            r0,EventStructPointer
add            r0,r10
ldr            r5,[r0]
ldr            r0,UnkIndex
add            r5,r5,r0
mov            r0,r8
mov            r1,r6
mov            r2,r7
mov            r3,#0x1
ldr            r4,GetItemNameText
bl             Longcall_4
mov            r1,r0
mov            r0,r5
ldr            r4,CopyString
bl             Longcall_4
b              MoveToNextEvent

RemoveItem:
mov            r0,r8
mov            r1,r6
mov            r2,r7
mov            r3,#0x1
ldr            r4,RemoveItemFromInventory
bl             Longcall_4
b              MoveToNextEvent

CheckForItem:
mov            r0,r8
mov            r1,r6
mov            r2,r7
ldr            r4,CountItemInInventory
bl             Longcall_4
cmp            r0,#0x0
bgt            MoveToNextEvent
ldr            r0,EventStructPointer
add            r0,r10
ldr            r1,[r0]
mov            r2,r9
ldr            r0,[r2,#0x4]
str            r0,[r1]
b              End

MoveToNextEvent:
ldr            r0,EventStructPointer
add            r0,r10
ldr            r2,[r0]
mov            r3,r9
ldrb           r1,[r3,#0x1]
ldr            r0,[r2]
add            r0,r0,r1
str            r0,[r2]
End:
mov            r0,#0x1
pop            {r3-r5}
mov            r8,r3
mov            r9,r4
mov            r10,r5
pop            {r4-r7}
pop            {r1}
bx             r1

.align 2
TradeQuestCounter:
.long       0x0000074C
UnkIndex:
.long       0x00001A5C
EventStructPointer:
.long       0x00007DAC

AddItemToInventory:
.long       0x0807EA15
GetItemNameText:
.long       0x0807EEB5
CountItemInInventory:
.long       0x0807EFBD
RemoveItemFromInventory:
.long       0x0807F029
GetVarMem:
.long		0x0807F15D

CopyString:
.long       0x08192355

EventItemList:
.long       0x082183B4
TradeQuestSelectionParams:
.long       0x08218954

Longcall_4:
bx            r4
