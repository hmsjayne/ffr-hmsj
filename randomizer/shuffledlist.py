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
from random import shuffle


class ShuffledList(object):
    """Class that can be used to shuffle a list of values, allowing acccess to the shuffled or original indexes.

    NOTE: This routine will advance the random number generator.
    """

    def __init__(self, values):
        if isinstance(values, (list, tuple)):
            self._backing_data = values
        else:
            self._backing_data = list(values)

        self._shuffled_indexes = list(range(len(self._backing_data)))
        shuffle(self._shuffled_indexes)

    def __getitem__(self, index):
        """Returns the shuffled item at the index.

        To retrieve the original value at [index], use [ShuffledList.original(index)]

        :param index: Index to retrieve the shuffled value from.
        :return: The shuffled value.
        """
        return self._backing_data[self._shuffled_indexes[index]]

    def original(self, index: int):
        """Returns the original item at the index.

        To retreive the shuffled value, use the index operator: ShuffledList[index]

        :param index: The index to retrieve the original value from.
        :return: The original value.
        """
        return self._backing_data[index]

    def original_index(self, index: int) -> int:
        """Returns the original index, given a shuffled index value.

        :param index: Index in the shuffled list
        :return: The original index
        """
        return self._shuffled_indexes[index]
