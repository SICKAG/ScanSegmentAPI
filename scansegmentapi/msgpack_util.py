#
# Copyright (c) 2023-2026 SICK AG
# SPDX-License-Identifier: MIT
#

"""This module contains functions to process data in the MSGPACK format.
"""

import msgpack

_KeywordIntegerLUT = {
    # General [0x10 - 0x2F]
    "class":                0x10,
    "data":                 0x11,
    "numOfElems":           0x12,
    "elemSz":              0x13,
    "endian":               0x14,
    "elemTypes":            0x15,
    # Constant values [0x30 - 0x4F]
    "little":              0x30,
    "float32":             0x31,
    "uint32":              0x32,
    "uint8":               0x33,
    "uint16":              0x34,
    "int16":               0x35,
    # Channels [0x50 - 0x6F]
    "ChannelTheta":        0x50,
    "ChannelPhi":          0x51,
    "DistValues":          0x52,
    "RssiValues":          0x53,
    "PropertiesValues":    0x54,
    # Scan fields [0x70 - 0x8F]
    "Scan":                0x70,
    "TimestampStart":      0x71,
    "TimestampStop":       0x72,
    "ThetaStart":          0x73,
    "ThetaStop":           0x74,
    "ScanNumber":          0x75,
    "ModuleID":            0x76,
    "BeamCount":           0x77,
    "EchoCount":           0x78,
    # Segment fields [0x90 - 0xAF]
    "ScanSegment":         0x90,
    "SegmentCounter":      0x91,
    "FrameNumber":         0x92,
    "Availability":        0x93,
    "SenderId":            0x94,
    "SegmentSize":         0x95,
    "SegmentData":         0x96,
    "LayerId":             0xA0,
    # Telegram Fields
    "TelegramCounter":     0xB0,
    "TimestampTransmit":    0xB1
}

_IntegerKeywordLUT = {value: key for (
    key, value) in _KeywordIntegerLUT.items()}


def unpack_msgpack_and_replace_integer_keywords(buffer: bytes) -> dict:
    """
    Unpacks the given MSGPACK structure. Integers are replaced by string keywords.

    Args:
        buffer (bytes): The buffer to unpack

    Returns:
        dict: The unpacked MSGPACK buffer
    """
    unpacked = msgpack.unpackb(buffer, strict_map_key=False)
    replace_keywords_in_dict(unpacked)
    return unpacked


def replace_keywords_in_dict(msgpack_value: dict) -> dict:
    """
    Replaces the integers in the given MSGPACK object serving as keywords with human-readable
    strings (see self.keywordIntegerLUT).

    Args:
        msgpack_value (dict): MSGPACK object for which to replace the integer keywords

    Returns:
        dict: The MSGPACK dictionary with replaced integer keys
    """
    if isinstance(msgpack_value, dict):
        int_keys = list(msgpack_value)
        for ikey in int_keys:
            string_key = _IntegerKeywordLUT[ikey]
            if string_key in ["class", "endian"]:
                msgpack_value[string_key] = _IntegerKeywordLUT[msgpack_value.pop(
                    ikey)]
            else:
                msgpack_value[string_key] = msgpack_value.pop(ikey)

            if isinstance(msgpack_value[string_key], dict):
                msgpack_value[string_key] = replace_keywords_in_dict(
                    msgpack_value[string_key])
            if isinstance(msgpack_value[string_key], list):
                for idx, elem in enumerate(msgpack_value[string_key]):
                    if string_key == "elemTypes":
                        msgpack_value[string_key][
                            idx] = _IntegerKeywordLUT[elem]
                    else:
                        elem = replace_keywords_in_dict(elem)
    return msgpack_value
