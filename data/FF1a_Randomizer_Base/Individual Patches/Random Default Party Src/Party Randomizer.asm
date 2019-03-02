@Little bit of code to randomize the default party
@Link from $4B3C8 with 0048 0047 XXXXXXXX
.thumb
ldr         r4,PartyData
add         r4,r9              @Location of party data
ldr         r4,[r4]
add         r4,#0xD            @Class ID byte location
ldr         r6,TakeRandom
ldr         r7,TakeRemainder
mov         r5,#0x3            @Repeat for all four party members
ClassAssignLoop:
bl          Longcall_6
lsl         r0,r0,#0x10
lsr         r0,r0,#0x10
mov         r1,#0x6            @Select any of the six basic classes
bl          Longcall_7
strb        r0,[r4]
add         r4,#0x48           @Move to next member's class byte loc
sub         r5,#0x1
cmp         r5,#0x0
bge         ClassAssignLoop
ldr         r7,ReturnAddress
bx          r7

.align 2
PartyData:
.long 0x00002F44
ReturnAddress:
.long 0x0804B3EB
TakeRandom:
.long 0x080696AD
TakeRemainder:
.long 0x08000F2D
Longcall_7:
bx          r7
Longcall_6:
bx          r6
