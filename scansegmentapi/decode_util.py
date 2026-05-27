#
# Copyright (c) 2023-2026 SICK AG
# SPDX-License-Identifier: MIT
#

"""This module contains helper functions which decode binary data contained in the
MSGPACK data format to numpy arrays
"""

import struct
import numpy as np


def decode_float_channel(channel: dict) -> np.array:
    """Interprets the binary data as an array of float32 values.

    Args:
        channel (dict): Dictionary containing the channel data and meta information

    Returns:
        np.array: Array of the decoded values
    """

    return _decode_channel(channel, 'f')


def decode_uint32_channel(channel: dict):
    """Interprets the binary data as an array of uint32 values.

    Args:
        channel (dict): Dictionary containing the channel data and meta information

    Returns:
        np.array: Array of the decoded values
    """
    return _decode_channel(channel, 'I')


def decode_uint16_channel(channel: dict):
    """Interprets the binary data as an array of uint16 values.

    Args:
        channel (dict): Dictionary containing the channel data and meta information

    Returns:
        np.array: Array of the decoded values
    """
    return _decode_channel(channel, 'H')


def decode_int16_channel(channel: dict):
    """Interprets the binary data as an array of int16 values.

    Args:
        channel (dict): Dictionary containing the channel data and meta information

    Returns:
        np.array: Array of the decoded values
    """
    return _decode_channel(channel, 'h')


def decode_uint8_channel(channel: dict):
    """Interprets the binary data as an array of uint8 values.

    Args:
        channel (dict): Dictionary containing the channel data and meta information

    Returns:
        np.array: Array of the decoded values
    """
    return _decode_channel(channel, 'B')


def _decode_channel(channel: dict, encoding_format: str) -> np.array:
    """Interprets the binary data as an array of values of the type specified in encoding_format.

    Args:
        channel (dict): dictionary containing the channel data and meta information
        encoding_format (str): The format that the data is encoded with

    Returns:
        np.array: Array of the decoded values
    """

    nb_beams = channel['numOfElems']
    # < explicitly states little endianess
    format_array = "<" + str(nb_beams) + encoding_format
    channel_data = np.asarray(struct.unpack(format_array, channel['data']))
    return channel_data
