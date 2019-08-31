#  Copyright 2019 Nicole Borrelli
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

from random import Random

class TreasureBuckets:
    def __init__(self):
        #For now, we're hard coding it. It's possible to change later
        self.buckets = {
            "Item_D": [0x01,0x0B,0x0D,0x0E,0x10,0x13],
            "Item_C": [0x02,0x04,0x0C,0x18,0x19,0x1A,0x1D],
            "Item_B": [0x05,0x09,0x0A,0x11,0x14,0x15,0x16,0x1B,0x20,0x22,0x24,0x25,0x26,0x29,0x2A],
            "Item_A": [0x03,0x06,0x07,0x12,0x17,0x1C,0x1E,0x1F,0x21,0x23,0x27,0x28,0x2B],
            "Item_S": [0x08,0x0F],
            "Weapon_D": [0x01,0x02,0x03,0x05,0x09,0x0A],
            "Weapon_C": [0x04,0x06,0x07,0x08,0x0B,0x0C,0x0D,0x0E,0x0F,0x1C],
            "Weapon_B": [0x10,0x11,0x12,0x13,0x16,0x17,0x19,0x1A,0x1B,0x1D,0x1E,0x1F,0x21,0x23,0x24,0x2F,0x31,0x33,0x35,0x3A,0x3B,0x3E],
            "Weapon_A": [0x14,0x15,0x18,0x20,0x22,0x25,0x26,0x27,0x2D,0x30,0x32,0x34,0x36,0x37,0x38,0x39,0x3D,0x3F,0x40],
            "Weapon_S": [0x28,0x29,0x2A,0x2B,0x2C,0x2E,0x3C],
            "Armor_D": [0x01,0x02,0x0B,0x1C,0x2A,0x2B,0x2C,0x3A,0x3B,0x3C],
            "Armor_C": [0x03,0x04,0x0C,0x1D,0x1E,0x23,0x2D,0x36,0x3D],
            "Armor_B": [0x05,0x06,0x0D,0x1A,0x1F,0x20,0x24,0x28,0x29,0x2E,0x35,0x38,0x3E,0x40,0x41,0x42,0x44,0x46],
            "Armor_A": [0x07,0x08,0x09,0x0E,0x10,0x12,0x13,0x14,0x16,0x17,0x21,0x22,0x2F,0x31,0x32,0x33,0x34,0x3F,0x43],
            "Armor_S": [0x0A,0x0F,0x11,0x15,0x18,0x19,0x1B,0x25,0x26,0x27,0x30,0x37,0x39,0x45],
        }
        #Okay but for real we need to set something up here
    
    def getBucket(self, itemType:int, id_val:int):
        if itemType == 1:
            if id_val in self.buckets["Item_D"]:
                return "Item_D"
            if id_val in self.buckets["Item_C"]:
                return "Item_C"
            if id_val in self.buckets["Item_B"]:
                return "Item_B"
            if id_val in self.buckets["Item_A"]:
                return "Item_A"
            if id_val in self.buckets["Item_S"]:
                return "Item_S"
        if itemType == 2:
            if id_val in self.buckets["Weapon_D"]:
                return "Weapon_D"
            if id_val in self.buckets["Weapon_C"]:
                return "Weapon_C"
            if id_val in self.buckets["Weapon_B"]:
                return "Weapon_B"
            if id_val in self.buckets["Weapon_A"]:
                return "Weapon_A"
            if id_val in self.buckets["Weapon_S"]:
                return "Weapon_S"
        if itemType == 3:
            if id_val in self.buckets["Armor_D"]:
                return "Armor_D"
            if id_val in self.buckets["Armor_C"]:
                return "Armor_C"
            if id_val in self.buckets["Armor_B"]:
                return "Armor_B"
            if id_val in self.buckets["Armor_A"]:
                return "Armor_A"
            if id_val in self.buckets["Armor_S"]:
                return "Armor_S"
        return None
    
    def up_one(self,tier):
        if tier.endswith("D"):
            return tier[:-1] + "C"
        if tier.endswith("C"):
            return tier[:-1] + "B"
        if tier.endswith("B"):
            return tier[:-1] + "A"
        if tier.endswith("A"):
            return tier[:-1] + "S"
        if tier.endswith("S"):
            return tier[:-1] + "S"
    
    def down_one(self,tier):
        if tier.endswith("D"):
            return tier[:-1] + "D"
        if tier.endswith("C"):
            return tier[:-1] + "D"
        if tier.endswith("B"):
            return tier[:-1] + "C"
        if tier.endswith("A"):
            return tier[:-1] + "B"
        if tier.endswith("S"):
            return tier[:-1] + "A"
    
    def pullFromBucket(self,bucket,rng,count: int):
        """Generate a list of items from a given bucket"""
        return rng.choices(self.buckets[bucket],k=count)
    
    def fullBucketList(self,buckets,rng,counts):
        """Generate a list of items, pulling a specified number from each bucket"""
        outList = []
        for i in range(len(buckets)):
            outList += self.pullFromBucket(buckets[i],counts[i])
        return outList