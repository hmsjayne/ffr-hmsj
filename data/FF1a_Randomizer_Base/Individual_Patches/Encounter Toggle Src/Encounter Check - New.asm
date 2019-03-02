@Does a check based on number of steps taken + RNG to see if you get an encounter this step
@Depending on your options byte, will load from one of two threshold sets or disable encounters
.thumb
push    	{r4,r5,r14}
mov     	r5,r1				@r5 = Area's Encounter Rate per step table
ldr     	r1,StepCounter
add     	r4,r0,r1
ldrb    	r0,[r4]				@Load step counter
cmp     	r0,#0x1F
bhi     	OptionCheck			@If taken thirty-two steps, do not increment
add     	r0,#0x1				@Otherwise, increment step counter
strb    	r0,[r4]
OptionCheck:
ldr         r0,VarMem
ldr         r0,[r0]             @Load base offset
mov         r1,#0xBA
lsl         r1,r1,#0x4          @Advance to options byte
ldrb        r1,[r0,r1]          @And load it!
lsr         r1,r1,#0x6          @Isolate the text speed byte
cmp         r1,#0x2
blt         CheckLoHi           @Are you in "off" mode?
mov         r0,#0x0
b           Return              @If so, no encounter no matter what
CheckLoHi:
cmp         r1,#0x1             @Are you in "low" mode?
bne         DoRNGCheck
mov         r1,#0xC0
lsl         r1,r1,#0x1
add         r5,r5,r1            @If so, go to the alternate encounter rates table
DoRNGCheck:
ldr     	r0,GenerateRandom	@Generate a random word
bl      	Longcall_0
lsr     	r0,r0,#0x16			@Take top 10 bits (value between 0x0 and 0x3FF)
ldrb    	r1,[r4]
lsl     	r1,r1,#0x1			@Advance to encounter rate for your current step
add     	r1,r1,r5
sub     	r1,#0x2				@since your step counter is always at least 1 at this stage
ldrh    	r1,[r1]				@Load the threshold value
cmp     	r0,r1				@If the random number is less than the threshold, get an encounter
bcc     	GetEncounter
mov     	r0,#0x0
b       	Return
GetEncounter:
mov     	r0,#0x0				@If you get an encounter, reset the step counter
strb    	r0,[r4]
mov     	r0,#0x1
Return:
pop     	{r4,r5}
pop     	{r1}
bx          r1

.align 2
VarMem:
.long       0x02000584
GenerateRandom:
.long		0x080696AD
StepCounter:
.long		0x00003826
Longcall_0:
bx				r0
