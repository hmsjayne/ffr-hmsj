#  Copyright 2020 Nicole Borrelli
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

import random
from doslib.rom import Rom
from doslib.enemy import *
from doslib.enemy import EnemyScript
from collections import namedtuple
from doslib.dos_utils import load_tsv
from stream.outputstream import OutputStream

NewScript = namedtuple("NewScript", ["iteration", "index", "name", "spell_chance", "ability_chance", 
                                     "spell_1", "spell_2", "spell_3", "spell_4", "spell_5", "spell_6", 
                                     "spell_7", "spell_8", "ability_1", "ability_2", "ability_3", "ability_4"])

maxBossIndex = 0xA0
maxScriptIndex = 0x3C
Fiend1Offsets = [119,121,123,125]
Fiend2Offsets = [120,122,124,126]
Fiend1ScriptOffsets = [34,36,38,40]
Fiend2ScriptOffsets = [35,37,39,41]

class BossData:
    def __init__(self, rom: Rom):
        # Initialize data - the 8 boss spots that are changed, as well as the name, graphics and script blocks
        # If we don't randomize anything, get_patches() should return the same data we load in
        name_pointers = rom.open_bytestream(0x1DDD38, 0x280)
        self.name_pointers = []
        while not name_pointers.is_eos():
            self.name_pointers.append(EnemyName(name_pointers))
            
        graphics_pointers = rom.open_bytestream(0x2227D8, 0x780)
        self.graphics_pointers = []
        while not graphics_pointers.is_eos():
            self.graphics_pointers.append(EnemyGraphics(graphics_pointers))
            
        attack_animations = rom.open_bytestream(0x223540, 0xA0)
        self.attack_animations = []
        while not attack_animations.is_eos():
            self.attack_animations.append(attack_animations.get_u8())
            
        enemy_script_stream = rom.open_bytestream(0x22F17C, 0x450)
        self.scripts = []
        while not enemy_script_stream.is_eos():
            self.scripts.append(EnemyScript(enemy_script_stream))
            
        self.bossData = {}
        for script in load_tsv("data/BossScriptData.tsv"):
            entry = NewScript(*script)
            if entry.name not in self.bossData:
                self.bossData[entry.name] = [None,None,None]
            self.bossData[entry.name][entry.iteration] = entry
        self.bossList = list(self.bossData.keys())
        
        #Finally, load in the script data from the ROM - we can read in the tsv if/when randomize gets called
    
    def randomize_bosses(self, rng: random.Random):
        bossChoices = rng.sample(self.bossList,4)
        rng.shuffle(bossChoices)
        newFiend1s = []
        newFiend1s.append(self.bossData[bossChoices[0]][0])
        newFiend1s.append(self.bossData[bossChoices[1]][0])
        newFiend1s.append(self.bossData[bossChoices[2]][1])
        newFiend1s.append(self.bossData[bossChoices[3]][1])
        
        newFiend2s = []
        newFiend2s.append(self.bossData[bossChoices[0]][2])
        newFiend2s.append(self.bossData[bossChoices[1]][2])
        newFiend2s.append(self.bossData[bossChoices[2]][2])
        newFiend2s.append(self.bossData[bossChoices[3]][2])
        
        for idx in range(4):
            fiend1 = newFiend1s[idx]
            fiend2 = newFiend2s[idx]
            self.graphics_pointers[Fiend1Offsets[idx]] = self.graphics_pointers[fiend1.index]
            self.graphics_pointers[Fiend2Offsets[idx]] = self.graphics_pointers[fiend2.index]
            self.attack_animations[Fiend1Offsets[idx]] = self.attack_animations[fiend1.index]
            self.attack_animations[Fiend2Offsets[idx]] = self.attack_animations[fiend2.index]
            self.name_pointers[Fiend1Offsets[idx]] = self.name_pointers[fiend1.index]
            self.name_pointers[Fiend2Offsets[idx]] = self.name_pointers[fiend2.index]
            
            fiend1Script = Fiend1ScriptOffsets[idx]
            
            self.scripts[fiend1Script].spell_chance = fiend1.spell_chance
            self.scripts[fiend1Script].ability_chance = fiend1.ability_chance
            self.scripts[fiend1Script].spell_1 = fiend1.spell_1
            self.scripts[fiend1Script].spell_2 = fiend1.spell_2
            self.scripts[fiend1Script].spell_3 = fiend1.spell_3
            self.scripts[fiend1Script].spell_4 = fiend1.spell_4
            self.scripts[fiend1Script].spell_5 = fiend1.spell_5
            self.scripts[fiend1Script].spell_6 = fiend1.spell_6
            self.scripts[fiend1Script].spell_7 = fiend1.spell_7
            self.scripts[fiend1Script].spell_8 = fiend1.spell_8
            self.scripts[fiend1Script].ability_1 = fiend1.ability_1
            self.scripts[fiend1Script].ability_2 = fiend1.ability_2
            self.scripts[fiend1Script].ability_3 = fiend1.ability_3
            self.scripts[fiend1Script].ability_4 = fiend1.ability_4
            
            fiend2Script = Fiend2ScriptOffsets[idx]
            
            self.scripts[fiend2Script].spell_chance = fiend2.spell_chance
            self.scripts[fiend2Script].ability_chance = fiend2.ability_chance
            self.scripts[fiend2Script].spell_1 = fiend2.spell_1
            self.scripts[fiend2Script].spell_2 = fiend2.spell_2
            self.scripts[fiend2Script].spell_3 = fiend2.spell_3
            self.scripts[fiend2Script].spell_4 = fiend2.spell_4
            self.scripts[fiend2Script].spell_5 = fiend2.spell_5
            self.scripts[fiend2Script].spell_6 = fiend2.spell_6
            self.scripts[fiend2Script].spell_7 = fiend2.spell_7
            self.scripts[fiend2Script].spell_8 = fiend2.spell_8
            self.scripts[fiend2Script].ability_1 = fiend2.ability_1
            self.scripts[fiend2Script].ability_2 = fiend2.ability_2
            self.scripts[fiend2Script].ability_3 = fiend2.ability_3
            self.scripts[fiend2Script].ability_4 = fiend2.ability_4
    
    def get_patches(self):
        out_name_pointers = OutputStream()
        for ptr in self.name_pointers:
            ptr.write(out_name_pointers)
        
        out_graphics_pointers = OutputStream()
        for ptr in self.graphics_pointers:
            ptr.write(out_graphics_pointers)
            
        out_attack_animations = OutputStream()
        for ptr in self.attack_animations:
            out_attack_animations.put_u8(ptr)
            
        out_scripts = OutputStream()
        for ptr in self.scripts:
            ptr.write(out_scripts)
        
        
        return {
            0x1DDD38: out_name_pointers.get_buffer(),
            0x2227D8: out_graphics_pointers.get_buffer(),
            0x223540: out_attack_animations.get_buffer(),
            0x22F17C: out_scripts.get_buffer()
        }
