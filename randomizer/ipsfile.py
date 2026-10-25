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

IPS_MAGIC = b'PATCH'
IPS_EOF = 0x454F46


def _data_source(data_source):
    if data_source is None:
        from doslib.data_source import FileSystemDataSource

        return FileSystemDataSource()
    return data_source


def load_ips_file(path, data_source=None):
    """Loads an IPS file into memory.

    :param path: Path to the IPS to load.
    :param data_source: Optional data source used to read the file.
    :return: A dictionary where the keys are the offset of the patch and the value is the data.
    """
    source = _data_source(data_source)
    data = source.read_bytes(str(path))
    index = len(IPS_MAGIC)
    if data[:index] != IPS_MAGIC:
        raise RuntimeError("File is not an IPS file (invalid header)")

    patch_data = dict()
    while True:
        offset = int.from_bytes(data[index:index + 3], byteorder="big", signed=False)
        index += 3
        if offset == IPS_EOF:
            break

        length = int.from_bytes(data[index:index + 2], byteorder="big", signed=False)
        index += 2
        if length == 0:
            run_length = int.from_bytes(data[index:index + 2], byteorder="big", signed=False)
            index += 2
            run_byte = data[index:index + 1]
            index += 1
            patch = run_byte * run_length
        else:
            patch = data[index:index + length]
            index += length

        patch_data[offset] = tuple(patch)

    return patch_data


def load_ips_files(*args, data_source=None) -> dict:
    """Loads a set of IPS files.

    :param args: List of IPS file paths to load.
    :param data_source: Optional data source used to read the files.
    :return: A dictionary containing all the offsets & data of the patches.
    """
    source = _data_source(data_source)
    complete = {}
    offset_file = {}
    loaded = []
    for file in args:
        if file in loaded:
            # IPS file has already be loaded, so skip reading it a second time.
            continue
        loaded.append(file)

        patches = load_ips_file(file, source)
        for offset, data in patches.items():
            if offset in complete:
                raise RuntimeWarning(f"Multiple patches targeted to {hex(offset)}: {file} vs {offset_file[offset]}")
            complete[offset] = data

            # Save data for debugging
            offset_file[offset] = file
    return complete


def apply_patches(data, patches):
    """Applies a set of patches to a block of data.

    :param data: The data to apply the patches to.
    :param patches: Patches to apply as a dictionary. Keys are offsets, values are patch data.
    :return: A patched version of the input data.
    """
    new_data = bytearray()

    working_offset = 0
    for offset in sorted(patches.keys()):
        if working_offset > offset:
            raise RuntimeError(f"Could not apply patch to {offset}; already at {working_offset}!")

        # Check if there's missing data between our working position and the next patch
        if working_offset < offset:
            new_data.extend(data[working_offset:offset])

        # Now that we're caught up, plop the patch in, and update the working offset.
        patch = patches[offset]
        new_data.extend(patch)
        working_offset = offset + len(patch)

    # Now that the patches are applied, add whatever is left of the file.
    new_data.extend(data[working_offset:])

    # Return the patched data as a tuple so it's immutable.
    return tuple(new_data)
