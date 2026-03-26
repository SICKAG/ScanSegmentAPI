#
# Copyright (c) 2023-2024 SICK AG
# SPDX-License-Identifier: MIT
#

from enum import Enum
import zlib
import logging

STX = b'\x02\x02\x02\x02'  # Marks the start of a Compact data package
COMMAND_ID = b'\x01\x00\x00\x00'  # Next field in the Compact header after STX
# Use both STX and COMMAND_ID as the delimiter to reduce false positives when identifying
# the potential start of a measurement data package.
DELIMITER = STX + COMMAND_ID
LENGTH_COMPACT_HEADER = 32
SIZE_OF_UINT32 = 4
SIZE_OF_CRC = 4
FIRST_MODULE_SIZE_OFFSET = 28
NUMBER_OF_LINES_OFFSET = 20
NEXT_MODULE_SIZE_OFFSET_PER_LINE = 28
NEXT_MODULE_SIZE_OFFSET = 36

logger = logging.getLogger("scansegmentapi")

class State(Enum):
    WAITING_FOR_STX = 1
    WAITING_FOR_HEADER = 2
    WAITING_FOR_MODULE_DATA = 3
    WAITING_FOR_CRC = 4


class CompactStreamExtractor():
    """
    This class extracts Compact V4 formatted data packages from a stream of bytes.
    A Compact data package is composed of the following parts:
        * Header: 32 bytes
        * Modules: variable size
        * CRC (Checksum): 4 bytes
    The first four bytes of the header are the STX (Start of TeXt) sequence.
    The following four bytes are the command ID.
    Bytes 28 to 31 specify the size of the first module.

    Each module has some meta data. In this meta data the size of the next module is specified.
    To get this size the bytes which come before this field need to be skipped.
    The number of bytes to skip depends on the number of lines in the module.
    The number of lines is also specified in the meta data at byte 20 to 23.
    Once the number of lines is extracted the position of the next module size can be calculated.
    The next module size is located at byte 32 + 32 * number of lines.
    The last module in a Compact data package has a next module size of 0.

    The last module is followed by a CRC which is calculated over the header and the modules.

    The extractor is a state machine which can be in one of the following states:
        * WAITING_FOR_STX: The extractor is searching for the STX sequence.
        * WAITING_FOR_HEADER: The extractor is waiting for the header to be complete.
        * WAITING_FOR_MODULE_DATA: The extractor is waiting for the next module to be complete.
        * WAITING_FOR_CRC: The extractor is waiting for the CRC to be complete.
    After each module, or at the beginning, the extractor is in the WAITING_FOR_STX state.
    As soon as the STX sequence is found in the data the extractor changes to the
    WAITING_FOR_HEADER state. As soon as enough data is available for the header the extractor
    changes to the WAITING_FOR_MODULE_DATA state. The header specifies the length of the first
    module. The extractor waits until enough data is available for the first module. Each module
    specifies the length of the next module. The extractor stays in the WAITING_FOR_MODULE_DATA
    state until the last module specifies a length of 0 for the next module then the extractor
    changes to the WAITING_FOR_CRC state. Once enough data for CRC has been received the extractor
    changes back to the WAITING_FOR_STX state  and adds one package
    with measurement data to the list of data packages which is returned
    by the extractor.
    """

    def __init__(self) -> None:
        """Create a new extractor instance.
        """
        self.buffer = bytes()
        self.state = State.WAITING_FOR_STX
        self.module_meta_data_position = 0
        self.payload_size = 0  # The size of all modules combined

    def _read_next_module_size(self, position: int) -> int:
        """Reads the next_module_size from a the given position.
        The user needs to ensure that the buffer is large enough to contain the next_module_size
        value.

        Args:
            position (int): Position in the buffer where the integer is located.

        Returns:
            int: The decoded module size.
        """
        next_module_size = self._decode_uint32(position)
        if next_module_size > 5e6:
            logger.warning("Got unusually large module size: ", next_module_size)
        return next_module_size

    def _decode_uint32(self, position: int) -> int:
        """Decodes an unsigned 32 bit integer at the given position.
        A byte order of little endian is assumed.

        Args:
            position (int): Position in the buffer where the integer is located.

        Returns:
            int: The decoded integer.
        """
        return int.from_bytes(
            self.buffer[position:position + SIZE_OF_UINT32], byteorder='little', signed=False)

    def _discard_stx(self):
        """Removes the number of bytes from the front of the buffer
        which are equal to the length of the STX sequence.
        """
        self.buffer = self.buffer[len(STX):]

    def _wait_for_stx(self) -> list[bytes]:
        """Searches for the STX sequence in the buffer.
        When the sequence is found the state is changed to WAITING_FOR_HEADER.

        Returns:
            list[bytes]: A list of data packages which were extracted from the buffer.
        """
        self.state = State.WAITING_FOR_STX
        stx_position = self.buffer.find(DELIMITER)
        if stx_position == -1:
            # No STX found in the buffer
            if len(self.buffer) >= len(DELIMITER):
                self.buffer = bytes()
            return []

        self.buffer = self.buffer[stx_position:]
        return self._wait_for_header()

    def _wait_for_header(self) -> list[bytes]:
        """Waits until there is enough data for the Compact header in the buffer.
        Reads the size of the first module from the header.
        Then the state is changed to WAITING_FOR_MODULE_DATA.

        Returns:
            list[bytes]: A list of data packages which were extracted from the buffer.
        """
        self.state = State.WAITING_FOR_HEADER
        if len(self.buffer) < LENGTH_COMPACT_HEADER:
            return []

        # Decode the size of the first module from the Compact header
        self.payload_size = self._read_next_module_size(FIRST_MODULE_SIZE_OFFSET)

        if self.payload_size == 0:
            logger.warning("The size of the first module must not be 0. Discarding STX.")
            self._discard_stx()
            return self._wait_for_stx()

        self.module_meta_data_position = LENGTH_COMPACT_HEADER

        return self._wait_for_module_data()

    def _wait_for_module_data(self) -> list[bytes]:
        """Waits until there is enough data for the next module in the buffer.
        Reads the size of the next module from the current module meta data.
        If the size is 0 the state is changed to WAITING_FOR_CRC otherwise
        waits for the data of the next module.

        Returns:
            list[bytes]: A list of data packages which were extracted from the buffer.
        """
        self.state = State.WAITING_FOR_MODULE_DATA

        # Check if the buffer contains enough data for: Compact header and the modules
        if len(self.buffer) < LENGTH_COMPACT_HEADER + self.payload_size:
            return []

        # Check if the buffer contains enough data for the number of lines field.
        # This check should always succeed due to the check above which makes sure that the buffer
        # contains at least the current module. However, in case that self.payload_size is
        # incorrect due to an error, we check here nevertheless that enough data for decoding the
        # uint32 value in the next statement is available in the buffer.
        if len(self.buffer) < \
           self.module_meta_data_position + NUMBER_OF_LINES_OFFSET + SIZE_OF_UINT32:
            return []

        # Extract the number of lines from the module meta data
        number_of_lines_in_module = self._decode_uint32(
            self.module_meta_data_position + NUMBER_OF_LINES_OFFSET
            )
        # The size of the next module is at byte:
        # 32 bytes independent of the number of lines + 32 bytes * per line
        next_module_size_position = self.module_meta_data_position + \
            NEXT_MODULE_SIZE_OFFSET + NEXT_MODULE_SIZE_OFFSET_PER_LINE * number_of_lines_in_module

        # Check if the buffer contains enough data for the next module size
        if len(self.buffer) < next_module_size_position + SIZE_OF_UINT32:
            return []

        next_module_size = self._read_next_module_size(next_module_size_position)

        if next_module_size == 0:
            return self._wait_for_crc()

        self.module_meta_data_position = LENGTH_COMPACT_HEADER + self.payload_size
        self.payload_size += next_module_size

        return self._wait_for_module_data()

    def _wait_for_crc(self) -> list[bytes]:
        """Waits until there is enough data for the CRC in the buffer.
        Compares the CRC from the buffer with the computed CRC.
        If they don't match the current STX is discarded.

        Returns:
            list[bytes]: A list of data packages which were extracted from the buffer.
        """
        self.state = State.WAITING_FOR_CRC
        # Check if the buffer contains enough data for: Compact header and the modules and the CRC
        if len(self.buffer) < LENGTH_COMPACT_HEADER + self.payload_size + SIZE_OF_CRC:
            return []

        # Extract the CRC
        expected_crc = self._decode_uint32(LENGTH_COMPACT_HEADER + self.payload_size)
        computed_crc = zlib.crc32(self.buffer[:LENGTH_COMPACT_HEADER + self.payload_size])
        if expected_crc != computed_crc:
            logger.warning("CRC failed. Not synchronized. Discarding STX.")
            self._discard_stx()
            return self._wait_for_stx()

        data_package = self.buffer[:LENGTH_COMPACT_HEADER + self.payload_size + SIZE_OF_CRC]
        self.buffer = self.buffer[LENGTH_COMPACT_HEADER + self.payload_size + SIZE_OF_CRC:]

        # The current data package is finished and added to the output list. With
        # self._wait_for_stx() the extraction of the next package in the buffer is triggered, if
        # there remains enough data in the buffer. The lists are concatenated with
        # the + operator
        return [data_package] + self._wait_for_stx()

    def extract_data_packages(self, data: bytes) -> list[bytes]:
        """Collects the data provided until one or more Compact data packages are complete.

        Args:
            data (bytes): A chunk of data which may contains parts of one or more
            Compact data packages.

        Returns:
            list[bytes]: A list of data packages which were extracted from previously and newly
            given data.
        """
        self.buffer += data

        if self.state == State.WAITING_FOR_STX:
            return self._wait_for_stx()

        if self.state == State.WAITING_FOR_HEADER:
            return self._wait_for_header()

        if self.state == State.WAITING_FOR_MODULE_DATA:
            return self._wait_for_module_data()

        if self.state == State.WAITING_FOR_CRC:
            return self._wait_for_crc()

        return []
