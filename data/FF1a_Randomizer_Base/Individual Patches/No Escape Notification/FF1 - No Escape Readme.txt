This is a hack for Final Fantasy I & II: Dawn of souls which makes unrunnable encounters display "No escape!" at the start of battle,
similar to the "Ambush" and "Preemptive strike" messages.
The specific changes are as follows:

-Unrunnable encounters will display a "No escape!" message:
	-Part 1, Initiative determination: Unrunnable stores 0x04 to memory
		$789B8: 1A49 515A 8800 4018 8000 0019 4778 8078 8046 BF00 002F 3DD1
	-Part 2, text display
		$76A78: 505C 8000 28D0 0149 0958 14E0 846A0708 BCA62208 A8A62208 9080EE8 9080EE8 E7480000
		(space until $76AAC free)
		$EE8090: Text for "No escape!" This is encoded in FF1+2's normal 2-byte text format.