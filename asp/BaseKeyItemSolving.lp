{pair(I,L) : location(L)} = 1 :- item(I).
{pair(I,L) : item(I)} = 1 :- location(L).

has(I) :- pair(I,L), open(L).

notHas(I) :- item(I), not has(I).

:- item(I), notHas(I).

#show notHas/1.
#show pair/2.

%Force fiends to be Vanilla
pair(earth,lich).
pair(fire,kary).
pair(water,kraken).
pair(air,tiamat).

%Debug stuff for PuwP
pair(bottle,caravan).

%Bahamut's event needs extra work
pair(promotion, bahamut).