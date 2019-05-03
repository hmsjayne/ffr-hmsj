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


class EndEventToken(str):
    pass


class LoadTextToken(str):
    pass


class LoadTextTopToken(int):
    pass


class LoadTextBottomToken(int):
    pass


class CloseDialogToken(str):
    pass


class CloseDialogAutoToken(int):
    pass


class CloseDialogWaitToken(int):
    pass


class JumpToken(str):
    pass


class JumpChestEmptyToken(str):
    pass


class MusicToken(str):
    pass


class SetRepeatToken(str):
    pass


class RepeatToken(str):
    pass


class ShowDialogToken(str):
    pass


class CheckFlagToken(str):
    pass


class SetFlagToken(str):
    pass


class JzToken(int):
    pass


class JnzToken(int):
    pass


class RemoveTriggerToken(str):
    pass


class NpcUpdateToken(str):
    pass


class SetNpcEventToken(str):
    pass


class RemoveAllToken(str):
    pass


class GiveItemToken(str):
    pass


class TakeItemToken(str):
    pass


class CheckItemToken(str):
    pass

class JumpByDirToken(str):
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
