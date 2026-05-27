#
# Copyright (c) 2024 SICK AG
# SPDX-License-Identifier: MIT
#

from enum import Enum
import zlib
import logging

STX = b'\x02\x02\x02\x02'  # Marks the start of a MSGPACK data package
SIZE_OF_UINT32 = 4
SIZE_OF_CRC = 4

logger = logging.getLogger("scansegmentapi")

class State(Enum):
    WAITING_FOR_STX = 1
    WAITING_FOR_SIZE = 2
    WAITING_FOR_CRC = 3


class MsgpackStreamExtractor():
    """
    This class extracts Msgpack formatted data packages from a stream of bytes.
    A Msgpack data package is composed of the following parts:
        * STX: 4 bytes
        * size: 4 bytes
        * MSGPACK buffer: variable size
        * CRC (Checksum): 4 bytes
    The first four bytes of the data package are the STX (Start of TeXt) sequence.
    The following four bytes are the size of the payload.
    The MSGPACK buffer is followed by a CRC which is calculated over the MSGPACK buffer.

    The extractor is a state machine which can be in one of the following states:
        * WAITING_FOR_STX: The extractor is searching for the STX sequence.
        * WAITING_FOR_SIZE: The extractor is waiting for the size of the MSGPACK buffer.
        * WAITING_FOR_CRC: The extractor is waiting for the CRC.
    After each data package, or at the beginning, the extractor is in the WAITING_FOR_STX state.
    As soon as the STX sequence is found in the data the extractor changes to the
    WAITING_FOR_SIZE state. As soon as enough data is available to read the size of the payload
    the extractor changes to the WAITING_FOR_CRC state. Once enough data for the payload and the
    CRC has been received the extractor changes back to the WAITING_FOR_STX state and adds one
    package with measurement data to the list of data packages which is returned by the extractor.
    """

    def __init__(self) -> None:
        """Create a new extractor instance.
        """
        self.buffer = bytes()
        self.state = State.WAITING_FOR_STX
        self.msgpack_size = 0

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
        When the sequence is found the state is changed to WAITING_FOR_SIZE.

        Returns:
            list[bytes]: A list of data packages which were extracted from the buffer.
        """
        self.state = State.WAITING_FOR_STX
        stx_position = self.buffer.find(STX)
        if stx_position == -1:  # No STX found in the buffer
            if len(self.buffer) >= len(STX):
                self.buffer = bytes()
            return []

        self.buffer = self.buffer[stx_position:]
        return self._wait_for_size()

    def _wait_for_size(self) -> list[bytes]:
        """Waits until there is enough data in the buffer to extract the size of the MSGPACK buffer.
        When the size is extracted the state is changed to WAITING_FOR_CRC.

        Returns:
            list[bytes]: A list of data packages which were extracted from the buffer.
        """
        self.state = State.WAITING_FOR_SIZE
        if len(self.buffer) < len(STX) + SIZE_OF_UINT32:
            return []

        # Decode the size of the MSGPACK buffer
        self.msgpack_size = self._decode_uint32(len(STX))

        if self.msgpack_size == 0:
            logger.warning("The size of the MSGPACK buffer must not be 0. Discarding STX.")
            self._discard_stx()
            return self._wait_for_stx()

        if self.msgpack_size > 5e6:
            logger.warning("Got unusually large MSGPACK buffer size: ", self.msgpack_size)

        return self._wait_for_crc()

    def _wait_for_crc(self) -> list[bytes]:
        """Waits until there is enough data for the CRC in the buffer.
        Compares the CRC from the buffer with the computed CRC.
        If they dont match the current STX is discarded.

        Returns:
            list[bytes]: A list of data packages which were extracted from the buffer.
        """
        self.state = State.WAITING_FOR_CRC

        if len(self.buffer) < len(STX) + SIZE_OF_UINT32 + self.msgpack_size + SIZE_OF_CRC:
            return []

        # Extract the CRC
        expected_crc = self._decode_uint32(len(STX) + SIZE_OF_UINT32 + self.msgpack_size)
        computed_crc = zlib.crc32(
            self.buffer[len(STX) + SIZE_OF_UINT32:len(STX) + SIZE_OF_UINT32 + self.msgpack_size])

        if expected_crc != computed_crc:
            logger.warning("CRC failed. Not synchronized. Discarding STX.")
            self._discard_stx()
            return self._wait_for_stx()

        data_package = self.buffer[:len(STX) + SIZE_OF_UINT32 + self.msgpack_size + SIZE_OF_CRC]
        self.buffer = self.buffer[len(STX) + SIZE_OF_UINT32 + self.msgpack_size + SIZE_OF_CRC:]

        # The current data package is finished and added to the output list. With
        # self._wait_for_stx() the extraction of the next package in the buffer is triggered, if
        # there remains enough data in the buffer. The lists are concatenated with
        # the + operator
        return [data_package] + self._wait_for_stx()

    def extract_data_packages(self, data: bytes) -> list[bytes]:
        """Collects the data provided until one or more Msgpack data packages are complete.

        Args:
            data (bytes): A chunk of data which may contains parts of, one,\
                 or more Msgpack data packages.

        Returns:
            list[bytes]: A list of data packages which were extracted \
                from previously and newly given data.
        """
        self.buffer += data

        if self.state == State.WAITING_FOR_STX:
            return self._wait_for_stx()

        if self.state == State.WAITING_FOR_SIZE:
            return self._wait_for_size()

        if self.state == State.WAITING_FOR_CRC:
            return self._wait_for_crc()

        return []
