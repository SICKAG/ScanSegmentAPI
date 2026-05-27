#
# Copyright (c) 2023-2026 SICK AG
# SPDX-License-Identifier: MIT
#

import struct
import pytest
from scansegmentapi import decode_util


def test_decode_single_zero_float_channel():
    channel = {
        "numOfElems": 1,
        "data": bytes([0x00, 0x00, 0x00, 0x00])
    }
    decoded = decode_util.decode_float_channel(channel)
    assert len(decoded) == 1
    assert decoded[0] == pytest.approx(0)


def test_decode_zeros_float_channel():
    numbeams = 100
    channel = {
        "numOfElems": numbeams,
        "data": bytes([0x00, 0x00, 0x00, 0x00] * numbeams)
    }
    decoded = decode_util.decode_float_channel(channel)
    assert len(decoded) == numbeams
    assert decoded[0] == pytest.approx(0)
    assert decoded[10] == pytest.approx(0)
    assert decoded[20] == pytest.approx(0)
    assert decoded[50] == pytest.approx(0)
    assert decoded[99] == pytest.approx(0)


def test_decode_generic_float_channel():
    channel = {
        "numOfElems": 6,
        "data": bytes(
            [0x00, 0x00, 0x00, 0x00] +  # 0.0
            [0x00, 0x00, 0x00, 0x3f] +  # 0.5
            [0x00, 0x00, 0x00, 0x40] +  # 2.0
            [0xfc, 0xa9, 0x2a, 0xc2] +  # -42.666
            [0xff, 0xff, 0x7f, 0xff] +  # float min
            [0xff, 0xff, 0x7f, 0x7f]  # float max
        )
    }

    decoded = decode_util.decode_float_channel(channel)
    assert len(decoded) == 6
    assert decoded[0] == pytest.approx(0)
    assert decoded[1] == pytest.approx(0.5)
    assert decoded[2] == pytest.approx(2.0)
    assert decoded[3] == pytest.approx(-42.666)
    assert decoded[
        4] == pytest.approx(-340282346638528859811704183484516925440)
    assert decoded[5] == pytest.approx(340282346638528859811704183484516925440)


def test_decode_empty_float_channel():
    channel = {
        "numOfElems": 0,
        "data": bytes()
    }
    decoded = decode_util.decode_float_channel(channel)
    assert len(decoded) == 0


def test_decode_float_channel_length_missmatch_zero_bytes():
    channel = {
        "numOfElems": 42,
        "data": bytes()
    }
    with pytest.raises(struct.error):
        decode_util.decode_float_channel(channel)


def test_decode_float_channel_length_missmatch():
    channel = {
        "numOfElems": 666,
        "data": bytes([0x00, 0x00, 0x00, 0x00] * 42)
    }
    with pytest.raises(struct.error):
        decode_util.decode_float_channel(channel)


def test_decode_single_zero_uint32_channel():
    channel = {
        "numOfElems": 1,
        "data": bytes([0x00, 0x00, 0x00, 0x00])
    }
    decoded = decode_util.decode_uint32_channel(channel)
    assert len(decoded) == 1
    assert decoded[0] == pytest.approx(0)


def test_decode_zeros_uint32_channel():
    numbeams = 100
    channel = {
        "numOfElems": numbeams,
        "data": bytes([0x00, 0x00, 0x00, 0x00] * numbeams)
    }
    decoded = decode_util.decode_uint32_channel(channel)
    assert len(decoded) == numbeams
    assert decoded[0] == 0
    assert decoded[10] == 0
    assert decoded[20] == 0
    assert decoded[50] == 0
    assert decoded[99] == 0


def test_decode_generic_uint32_channel():
    channel = {
        "numOfElems": 4,
        "data": bytes(
            [0x00, 0x00, 0x00, 0x00] +  # 0.0
            [0x2a, 0x00, 0x00, 0x00] +  # 42
            [0x9a, 0x02, 0x00, 0x00] +  # 666
            [0xff, 0xff, 0xff, 0xff]  # 2^32 - 1
        )
    }

    decoded = decode_util.decode_uint32_channel(channel)
    assert len(decoded) == 4
    assert decoded[0] == 0
    assert decoded[1] == 42
    assert decoded[2] == 666
    assert decoded[3] == (2 ** 32) - 1


def test_decode_empty_uint32_channel():
    channel = {
        "numOfElems": 0,
        "data": bytes()
    }
    decoded = decode_util.decode_uint32_channel(channel)
    assert len(decoded) == 0


def test_decode_uint32_channel_length_missmatch_zero_bytes():
    channel = {
        "numOfElems": 42,
        "data": bytes()
    }
    with pytest.raises(struct.error):
        decode_util.decode_uint32_channel(channel)


def test_decode_uint32_channel_length_missmatch():
    channel = {
        "numOfElems": 666,
        "data": bytes([0x00, 0x00, 0x00, 0x00] * 42)
    }
    with pytest.raises(struct.error):
        decode_util.decode_uint32_channel(channel)


def test_decode_single_zero_uint16_channel():
    channel = {
        "numOfElems": 1,
        "data": bytes([0x00, 0x00])
    }
    decoded = decode_util.decode_uint16_channel(channel)
    assert len(decoded) == 1
    assert decoded[0] == pytest.approx(0)


def test_decode_zeros_uint16_channel():
    numbeams = 100
    channel = {
        "numOfElems": numbeams,
        "data": bytes([0x00, 0x00] * numbeams)
    }
    decoded = decode_util.decode_uint16_channel(channel)
    assert len(decoded) == numbeams
    assert decoded[0] == 0
    assert decoded[10] == 0
    assert decoded[20] == 0
    assert decoded[50] == 0
    assert decoded[99] == 0


def test_decode_generic_uint16_channel():
    channel = {
        "numOfElems": 4,
        "data": bytes(
            [0x00, 0x00] +  # 0.0
            [0x2a, 0x00] +  # 42
            [0x9a, 0x02] +  # 666
            [0xff, 0xff]  # 2^16 - 1
        )
    }

    decoded = decode_util.decode_uint16_channel(channel)
    assert len(decoded) == 4
    assert decoded[0] == 0
    assert decoded[1] == 42
    assert decoded[2] == 666
    assert decoded[3] == (2 ** 16) - 1


def test_decode_empty_uint16_channel():
    channel = {
        "numOfElems": 0,
        "data": bytes()
    }
    decoded = decode_util.decode_uint16_channel(channel)
    assert len(decoded) == 0


def test_decode_uint16_channel_length_missmatch_zero_bytes():
    channel = {
        "numOfElems": 42,
        "data": bytes()
    }
    with pytest.raises(struct.error):
        decode_util.decode_uint16_channel(channel)


def test_decode_uint16_channel_length_missmatch():
    channel = {
        "numOfElems": 666,
        "data": bytes([0x00, 0x00] * 42)
    }
    with pytest.raises(struct.error):
        decode_util.decode_uint16_channel(channel)


def test_decode_single_zero_int16_channel():
    channel = {
        "numOfElems": 1,
        "data": bytes([0x00, 0x00])
    }
    decoded = decode_util.decode_int16_channel(channel)
    assert len(decoded) == 1
    assert decoded[0] == pytest.approx(0)


def test_decode_zeros_int16_channel():
    numbeams = 100
    channel = {
        "numOfElems": numbeams,
        "data": bytes([0x00, 0x00] * numbeams)
    }
    decoded = decode_util.decode_int16_channel(channel)
    assert len(decoded) == numbeams
    assert decoded[0] == 0
    assert decoded[10] == 0
    assert decoded[20] == 0
    assert decoded[50] == 0
    assert decoded[99] == 0


def test_decode_generic_int16_channel():
    channel = {
        "numOfElems": 4,
        "data": bytes(
            [0x00, 0x00] +  # 0.0
            [0xff, 0x7f] +  # 2^15 - 1
            [0x00, 0x80] +  # -(2^15)
            [0x2a, 0x00]  # 42
        )
    }

    decoded = decode_util.decode_int16_channel(channel)
    assert len(decoded) == 4
    assert decoded[0] == 0
    assert decoded[1] == (2 ** 15) - 1
    assert decoded[2] == -(2 ** 15)
    assert decoded[3] == 42


def test_decode_empty_int16_channel():
    channel = {
        "numOfElems": 0,
        "data": bytes()
    }
    decoded = decode_util.decode_int16_channel(channel)
    assert len(decoded) == 0


def test_decode_int16_channel_length_missmatch_zero_bytes():
    channel = {
        "numOfElems": 42,
        "data": bytes()
    }
    with pytest.raises(struct.error):
        decode_util.decode_int16_channel(channel)


def test_decode_int16_channel_length_missmatch():
    channel = {
        "numOfElems": 666,
        "data": bytes([0x00, 0x00] * 42)
    }
    with pytest.raises(struct.error):
        decode_util.decode_int16_channel(channel)


def test_decode_single_zero_uint8_channel():
    channel = {
        "numOfElems": 1,
        "data": bytes([0x00])
    }
    decoded = decode_util.decode_uint8_channel(channel)
    assert len(decoded) == 1
    assert decoded[0] == pytest.approx(0)


def test_decode_zeros_uint8_channel():
    numbeams = 100
    channel = {
        "numOfElems": numbeams,
        "data": bytes([0x00] * numbeams)
    }
    decoded = decode_util.decode_uint8_channel(channel)
    assert len(decoded) == numbeams
    assert decoded[0] == 0
    assert decoded[10] == 0
    assert decoded[20] == 0
    assert decoded[50] == 0
    assert decoded[99] == 0


def test_decode_generic_uint8_channel():
    channel = {
        "numOfElems": 4,
        "data": bytes(
            [0x00] +  # 0.0
            [0xff] +  # 2^8 - 1
            [0x18] +  # 24
            [0x2a]  # 42
        )
    }

    decoded = decode_util.decode_uint8_channel(channel)
    assert len(decoded) == 4
    assert decoded[0] == 0
    assert decoded[1] == (2 ** 8) - 1
    assert decoded[2] == 24
    assert decoded[3] == 42


def test_decode_empty_uint8_channel():
    channel = {
        "numOfElems": 0,
        "data": bytes()
    }
    decoded = decode_util.decode_uint8_channel(channel)
    assert len(decoded) == 0


def test_decode_uint8_channel_length_missmatch_zero_bytes():
    channel = {
        "numOfElems": 42,
        "data": bytes()
    }
    with pytest.raises(struct.error):
        decode_util.decode_uint8_channel(channel)


def test_decode_uint8_channel_length_missmatch():
    channel = {
        "numOfElems": 666,
        "data": bytes([0x00] * 42)
    }
    with pytest.raises(struct.error):
        decode_util.decode_uint8_channel(channel)
