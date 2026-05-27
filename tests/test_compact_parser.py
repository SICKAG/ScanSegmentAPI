#
# Copyright (c) 2023-2026 SICK AG
# SPDX-License-Identifier: MIT
#
import math
import pytest

import scansegmentapi.compact as compactApi


def test_parse_sample_compact(sample_file):
    """
    Just parse a sample serialized to a Compact formatted binary file.
    """
    parsed_segment = compactApi.parse_from_file(sample_file("sample.compact"))

    assert parsed_segment["TelegramCounter"] == 333
    assert parsed_segment["TimestampTransmit"] == 444
    modules = parsed_segment["Modules"]
    assert len(modules) == 2

    module_1 = modules[0]
    assert module_1["SegmentCounter"] == 666
    assert module_1["FrameNumber"] == 999
    assert module_1["Availability"]
    assert module_1["NumberOfLinesInModule"] == 1
    assert module_1["SenderId"] == 555
    assert module_1["NumberOfBeamsPerScan"] == 10
    assert module_1["NumberOfEchosPerBeam"] == 2
    assert len(module_1["ThetaStart"]) == 1
    assert module_1["ThetaStart"] == pytest.approx([math.radians(0)])
    assert len(module_1["ThetaStop"]) == 1
    assert module_1["ThetaStop"] == pytest.approx([math.radians(9)])
    assert len(module_1["TimestampStart"]) == 1
    assert len(module_1["TimestampStop"]) == 1

    assert module_1["HasDistance"]
    assert module_1["HasRssi"]
    assert not module_1["HasProperties"]
    assert module_1["HasTheta"]

    assert len(module_1["SegmentData"]) == 1
    segment_data = module_1["SegmentData"][0]

    assert len(segment_data["Rssi"]) == 2
    assert segment_data["Rssi"][0] == pytest.approx(
        [21036, 21036, 21036, 21036, 21036, 21036, 21036, 21036, 21036, 21036])
    assert segment_data["Rssi"][1] == pytest.approx(
        [21036, 21036, 21036, 21036, 21036, 21036, 21036, 21036, 21036, 21036])

    assert len(segment_data["Distance"]) == 2
    assert segment_data["Distance"][0] == pytest.approx(
        [123, 123, 123, 123, 123, 123, 123, 123, 123, 123])
    assert segment_data["Distance"][1] == pytest.approx(
        [123, 123, 123, 123, 123, 123, 123, 123, 123, 123])

    assert segment_data["ChannelTheta"] == pytest.approx([
        math.radians(0), math.radians(1), math.radians(2), math.radians(3), math.radians(4),
        math.radians(5), math.radians(6), math.radians(7), math.radians(8), math.radians(9)
    ], abs=1e-3)

    module_2 = modules[1]
    assert module_2["SegmentCounter"] == 666
    assert module_2["FrameNumber"] == 999
    assert module_2["Availability"]
    assert module_2["NumberOfLinesInModule"] == 1
    assert module_2["SenderId"] == 555
    assert module_2["NumberOfBeamsPerScan"] == 10
    assert module_2["NumberOfEchosPerBeam"] == 2
    assert len(module_2["ThetaStart"]) == 1
    assert module_2["ThetaStart"] == pytest.approx([math.radians(90)])
    assert len(module_2["ThetaStop"]) == 1
    assert module_2["ThetaStop"] == pytest.approx([math.radians(99)])
    assert len(module_2["TimestampStart"]) == 1
    assert len(module_2["TimestampStop"]) == 1

    assert module_2["HasDistance"]
    assert module_2["HasRssi"]
    assert not module_2["HasProperties"]
    assert module_2["HasTheta"]

    assert len(module_2["SegmentData"]) == 1
    segment_data = module_2["SegmentData"][0]

    assert len(segment_data["Rssi"]) == 2
    assert segment_data["Rssi"][0] == pytest.approx(
        [44432, 44432, 44432, 44432, 44432, 44432, 44432, 44432, 44432, 44432])
    assert segment_data["Rssi"][1] == pytest.approx(
        [44432, 44432, 44432, 44432, 44432, 44432, 44432, 44432, 44432, 44432])

    assert len(segment_data["Distance"]) == 2
    assert segment_data["Distance"][0] == pytest.approx(
        [456, 456, 456, 456, 456, 456, 456, 456, 456, 456])
    assert segment_data["Distance"][1] == pytest.approx(
        [456, 456, 456, 456, 456, 456, 456, 456, 456, 456])

    assert segment_data["ChannelTheta"] == pytest.approx([
        math.radians(90), math.radians(91), math.radians(92), math.radians(93), math.radians(94),
        math.radians(95), math.radians(96), math.radians(97), math.radians(98), math.radians(99)
    ], abs=1e-3)
