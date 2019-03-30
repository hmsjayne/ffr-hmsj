
locked(L) :- requires(L,_).
unlocked(L) :- location(L), not locked(L).

{pair(I,L) : location(L)} = 1 :- item(I).
{pair(I,L) : item(I)} = 1 :- location(L).

has(I) :- pair(I,L), unlocked(L).
has(sky_access) :- has(chime), has(cube).
has(I) :- pair(I,L), has(I2), requires(L,I2).
    
notHas(I) :- item(I), not has(I).

:- item(I), notHas(I).
    
#show notHas/1.
#show pair/2.