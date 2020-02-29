item(lute).
item(bridge).
item(ship).
item(crown).
item(crystal).
item(jolt_tonic).
item(mystic_key).
item(nitro_powder).
item(canal).
item(star_ruby).
item(rod).
item(canoe).
item(levistone).
item(airship).
item(rats_tail).
item(promotion).
item(bottle).
item(oxyale).
item(rosetta_stone).
item(lufienish).
item(chime).
item(warp_cube).
item(adamantite).
item(excalibur).
item(earth).
item(fire).
item(water).
item(air).

location(sara).
location(king).
location(bikke).
location(marsh).
location(astos).
location(matoya).
location(elf).
location(locked_cornelia).
location(nerrick).
location(vampire).
location(sarda).
location(lukahn).
location(ice).
location(desert).
location(citadel_of_trials).
location(caravan).
location(fairy).
location(mermaids).
location(lefien).
location(waterfall).
location(sky2).
location(smyth).
location(lich).
location(kary).
location(kraken).
location(tiamat).
location(bahamut).
location(dr_unne).

open(king).
open(sara).
open(bikke) :- has(bridge).
open(bikke) :- has(ship).
open(bikke) :- has(airship).
open(marsh) :- has(ship).
open(marsh) :- has(airship).
open(astos) :- has(ship), has(crown).
open(astos) :- has(airship), has(crown).
open(matoya) :- has(bridge), has(crystal).
open(matoya) :- has(ship), has(crystal).
open(matoya) :- has(airship), has(crystal).
open(elf) :- has(ship), has(jolt_tonic).
open(locked_cornelia) :- has(mystic_key).
open(nerrick) :- has(ship), has(nitro_powder).
open(nerrick) :- has(airship), has(nitro_powder).
open(vampire) :- has(airship).
open(vampire) :- has(ship), has(canal).
open(sarda) :- has(star_ruby), has(airship).
open(sarda) :- has(ship), has(canal), has(star_ruby).
open(sarda) :- has(airship), has(star_ruby).
open(lukahn) :- has(airship), has(earth).
open(lukahn) :- has(ship), has(canal), has(earth).
open(lukahn) :- has(ship), has(canoe), has(earth).
open(ice) :- has(bridge), has(canoe).
open(ice) :- has(ship), has(canoe).
open(desert) :- has(ship), has(canoe), has(levistone).
open(desert) :- has(airship), has(levistone).
open(citadel_of_trials) :- has(ship), has(canal), has(canoe), has(crown).
open(citadel_of_trials) :- has(airship), has(canoe), has(crown).
open(caravan) :- has(airship).
open(fairy) :- has(airship), has(bottle).
open(mermaids) :- has(airship), has(oxyale).
open(lefien) :- has(airship), has(lufienish).
open(waterfall) :- has(airship), has(canoe).
open(sky2) :- has(airship), has(chime), has(warp_cube).
open(smyth) :- has(ship), has(adamantite).
open(smyth) :- has(airship), has(adamantite).
open(lich) :- has(rod), has(ship), has(canal).
open(lich) :- has(rod), has(airship).
open(kary) :- has(ship), has(canoe).
open(kary) :- has(airship).
open(kraken) :- has(airship), has(oxyale).
open(tiamat) :- has(airship), has(chime), has(warp_cube).
open(bahamut) :- has(rats_tail), has(airship).
open(dr_unne) :- has(ship), has(canal), has(rosetta_stone).
open(dr_unne) :- has(airship), has(rosetta_stone).
