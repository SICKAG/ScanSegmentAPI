#
# Copyright (c) 2023 SICK AG
# SPDX-License-Identifier: MIT
#
import api.msgpack as msgpackApi

import math
import pytest


def test_parse_sample_msgpack(sample_file):
    """
    Just parse a sample serialized to a MSGPACK formatted binary file.
    """
    parsed_segment, _, _ = msgpackApi.parseFromFile(sample_file("sample.msgpack"))

    assert parsed_segment["TelegramCounter"] == 333
    assert parsed_segment["TimestampTransmit"] == 444
    assert parsed_segment["SenderId"] == 555
    assert parsed_segment["Availability"] == True
    assert parsed_segment["SegmentCounter"] == 666
    assert parsed_segment["FrameNumber"] == 999
    assert parsed_segment["LayerId"] == [1, 2]
    assert len(parsed_segment["SegmentData"]) == 2

    scan_1 = parsed_segment["SegmentData"][0]
    assert scan_1["BeamCount"] == 10
    assert scan_1["EchoCount"] == 2
    assert scan_1["ThetaStart"] == pytest.approx(math.radians(0))
    assert scan_1["ThetaStop"] == pytest.approx(math.radians(9))
    assert scan_1["ScanNumber"] == 22
    assert scan_1["ModuleID"] == 54

    assert len(scan_1["Rssi"]) == 2
    assert scan_1["Rssi"][0] == pytest.approx([21036, 21036, 21036, 21036, 21036, 21036, 21036, 21036, 21036, 21036])
    assert scan_1["Rssi"][1] == pytest.approx([21036, 21036, 21036, 21036, 21036, 21036, 21036, 21036, 21036, 21036])

    assert len(scan_1["Distance"]) == 2
    assert scan_1["Distance"][0] == pytest.approx([123.456, 123.456, 123.456, 123.456, 123.456, 123.456, 123.456, 123.456, 123.456, 123.456])
    assert scan_1["Distance"][1] == pytest.approx([123.456, 123.456, 123.456, 123.456, 123.456, 123.456, 123.456, 123.456, 123.456, 123.456])

    assert scan_1["ChannelTheta"] == pytest.approx([
        math.radians(0), math.radians(1), math.radians(2), math.radians(3), math.radians(4),
        math.radians(5), math.radians(6), math.radians(7), math.radians(8), math.radians(9)
    ], abs=1e-3)

    scan_2 = parsed_segment["SegmentData"][1]
    assert scan_2["BeamCount"] == 10
    assert scan_2["EchoCount"] == 2
    assert scan_2["ThetaStart"] == pytest.approx(math.radians(90))
    assert scan_2["ThetaStop"] == pytest.approx(math.radians(99))
    assert scan_2["ScanNumber"] == 11
    assert scan_2["ModuleID"] == 56

    assert len(scan_2["Rssi"]) == 2
    assert scan_2["Rssi"][0] == pytest.approx([44432, 44432, 44432, 44432, 44432, 44432, 44432, 44432, 44432, 44432])
    assert scan_2["Rssi"][1] == pytest.approx([44432, 44432, 44432, 44432, 44432, 44432, 44432, 44432, 44432, 44432])

    assert len(scan_2["Distance"]) == 2
    assert scan_2["Distance"][0] == pytest.approx([456.123, 456.123, 456.123, 456.123, 456.123, 456.123, 456.123, 456.123, 456.123, 456.123])
    assert scan_2["Distance"][1] == pytest.approx([456.123, 456.123, 456.123, 456.123, 456.123, 456.123, 456.123, 456.123, 456.123, 456.123])

    assert scan_2["ChannelTheta"] == pytest.approx([
        math.radians(90), math.radians(91), math.radians(92), math.radians(93), math.radians(94),
        math.radians(95), math.radians(96), math.radians(97), math.radians(98), math.radians(99)
    ], abs=1e-3)
