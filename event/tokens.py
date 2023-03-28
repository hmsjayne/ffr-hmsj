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

# This file defines the various tokens used by easm.


class CommentToken(str):
    pass


class LabelToken(str):
    pass


class SymbolToken(str):
    pass


class ColonToken(str):
    pass


class NumberToken(int):
    def __repr__(self):
        return f"NumberToken({hex(self)})"

    def __str__(self):
        return f"NumberToken({hex(self)})"


class RawCommandToken(str):
    pass


class EndEventToken(list):
    pass


class NopToken(list):
    pass


class LoadMapToken(list):
    pass


class LoadTextToken(list):
    pass


class CloseDialogToken(list):
    pass


class DelayToken(list):
    pass


class MoveNpcToken(list):
    pass


class JumpToken(list):
    pass


class JumpChestEmptyToken(list):
    pass


class MusicToken(list):
    pass


class AddNpcToken(list):
    pass


class RemoveNpcToken(list):
    pass


class MovePartyToken(list):
    pass


class SetRepeatToken(list):
    pass


class RepeatToken(list):
    pass


class SetNpcFrameToken(list):
    pass


class ShowDialogToken(list):
    pass


class CheckFlagToken(list):
    pass


class SetFlagToken(list):
    pass


class JzToken(int):
    pass


class JnzToken(int):
    pass


class RemoveTriggerToken(list):
    pass


class NpcUpdateToken(list):
    pass


class SetNpcEventToken(list):
    pass


class RemoveAllToken(list):
    pass


class GiveItemToken(list):
    pass


class GiveItemExtendedToken(list):
    pass


class TakeItemToken(list):
    pass


class CheckItemToken(list):
    pass


class PromotePcsToken(list):
    pass


class JumpByDirToken(list):
    pass


class CallToken(list):
    pass


class Uint16(object):
    def __init__(self, value: int):
        self._value = value

    def __repr__(self):
        return f"Unit16({hex(self._value)})"

    def bytes(self):
        return [self._value & 0xff, (self._value >> 8) & 0xff]


class Uint32(object):
    def __init__(self, value: int):
        self._value = value

    def __repr__(self):
        return f"Uint32({hex(self._value)})"

    def bytes(self):
        return [self._value & 0xff, (self._value >> 8) & 0xff, (self._value >> 16) & 0xff, (self._value >> 24) & 0xff]
