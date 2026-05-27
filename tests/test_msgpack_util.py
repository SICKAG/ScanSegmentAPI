#
# Copyright (c) 2023-2026 SICK AG
# SPDX-License-Identifier: MIT
#

import msgpack
from scansegmentapi import msgpack_util


def test_single_key_is_replaced_correctly():
    integer_keys = msgpack.packb({0xA0: "Test"})
    string_keys = {"LayerId": "Test"}

    assert msgpack_util.unpack_msgpack_and_replace_integer_keywords(
        integer_keys) == string_keys


def test_multiple_keys_are_replaced_correctly():
    integer_keys = msgpack.packb({0xA0: "Test", 0x52: 42})
    string_keys = {"LayerId": "Test", "DistValues": 42}

    assert msgpack_util.unpack_msgpack_and_replace_integer_keywords(
        integer_keys) == string_keys


def test_nested_dicts_are_replaced_correctly():
    integer_keys = msgpack.packb({0xA0: {0x52: 42}})
    string_keys = {"LayerId": {"DistValues": 42}}

    assert msgpack_util.unpack_msgpack_and_replace_integer_keywords(
        integer_keys) == string_keys


def test_list_of_dicts_are_replaced_correctly():
    integer_keys = msgpack.packb(
        {
            0x11: [
                {0x50: 42},
                {0x51: 43},
                {0x52: 44}
            ]
        }
    )
    string_keys = {
        "data": [
            {"ChannelTheta": 42},
            {"ChannelPhi": 43},
            {"DistValues": 44}
        ]
    }

    assert msgpack_util.unpack_msgpack_and_replace_integer_keywords(
        integer_keys) == string_keys


def test_value_of_class_key_is_replaced():
    integer_keys = msgpack.packb(
        {
            0x10: 0x70
        }
    )
    string_keys = {
        "class": "Scan"
    }

    assert msgpack_util.unpack_msgpack_and_replace_integer_keywords(
        integer_keys) == string_keys


def test_value_of_endian_key_is_replaced():
    integer_keys = msgpack.packb(
        {
            0x14: 0x30
        }
    )
    string_keys = {
        "endian": "little"
    }

    assert msgpack_util.unpack_msgpack_and_replace_integer_keywords(
        integer_keys) == string_keys


def test_data_types_are_replaced_correctly():
    integer_keys = msgpack.packb(
        {
            0x15: [0x31, 0x32, 0x33, 0x34, 0x35]
        }
    )
    string_keys = {
        "elemTypes": ["float32", "uint32", "uint8", "uint16", "int16"]
    }

    assert msgpack_util.unpack_msgpack_and_replace_integer_keywords(
        integer_keys) == string_keys
