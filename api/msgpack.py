#
# Copyright (c) 2023 SICK AG
# SPDX-License-Identifier: MIT
#
from scansegmentdecoding import connectionHandler
from scansegmentdecoding import msgpackUtil
from scansegmentdecoding import decodeUtil

import sys
import zlib


def parseFromFile(filename):
    """
    Reads a Msgpack formatted binary file and parses its content to a dictionary.
    """
    with open(filename, "rb") as f:
        print(f"Parsing {filename}...")
        byte_data = f.read()
        return parsePayload(byte_data)


def parsePayload(payload):
    """
    Parses the given payload as byte array into a dictionary. Along with the dictionary the frame number and segment
    number of the parsed segment are returned.
    """
    data_dict = msgpackUtil.UnpackMsgpackAndReplaceIntegerKeywords(payload)

    # Extract meta data.
    segment = {
        'Availability': data_dict['data']['Availability'],
        'FrameNumber': data_dict['data']['FrameNumber'],
        'SegmentCounter': data_dict['data']['SegmentCounter'],
        'SenderId': data_dict['data']['SenderId'],
        'TelegramCounter': data_dict['data']['TelegramCounter'],
        'TimestampTransmit': data_dict['data']['TimestampTransmit'],
        'LayerId': data_dict['data']['LayerId'],
        # Extract actual segment data.
        'SegmentData': _extractSegmentData(data_dict['data']['SegmentData'])
    }
    return (segment, segment['FrameNumber'], segment['SegmentCounter'])


def _verifyAndExtractPayload(data):
    """
    Checks if the payload contained in the given byte array is complete. The extracted payload is returned if it is
    the case. Otherweise None is returned.
    """
    bytes_frame_start = data[0:4]
    bytes_payload_length = data[4:8]
    bytes_payload = data[8:-4]
    # CRC is computed over payload only without the frame start and length bytes.
    bytes_crc = data[-4:len(data)]

    # Check if frame header is included.
    if b'\x02\x02\x02\x02' != bytes_frame_start:
        print(
            "Missing start of frame sequence [0x02 0x02 0x02 0x02].", file=sys.stderr)
        return None

    # Check if received payload length matches expected one.
    expected_payload_length = int.from_bytes(bytes_payload_length, 'little')
    if expected_payload_length != len(bytes_payload):
        print(
            f"Actual length of payload and expected length do not match. Expected {expected_payload_length} bytes, got {len(bytes_payload)}.", file=sys.stderr)
        return None

    # Apply CRC.
    expected_crc = int.from_bytes(bytes_crc, 'little')
    computed_crc = zlib.crc32(bytes_payload)
    if expected_crc != computed_crc:
        print(
            "CRC failed. Expected {expected_crc}, got {computed_crc}.", file=sys.stderr)
        return None

    return bytes_payload


def _extractSegmentData(segment_data_raw):
    """
    Extracts the actual data value contained in the segment (namely distances, RSSIs and properties) along with
    the metadata of each single layer. Returned is an array of dictionaries where each array item corresponds to
    a single layer.
    """
    segmentdata = []
    for scan in segment_data_raw:
        scandata = {
            'TimestampStart': scan['data']['TimestampStart'],
            'TimestampStop': scan['data']['TimestampStop'],
            'ThetaStart': scan['data']['ThetaStart'],
            'ThetaStop': scan['data']['ThetaStop'],
            'ScanNumber': scan['data']['ScanNumber'],
            'ModuleID': scan['data']['ModuleID'],
            'BeamCount': scan['data']['BeamCount'],
            'EchoCount': scan['data']['EchoCount'],
            # Phi is constant for a single layer so we just select the very first one.
            'Phi': decodeUtil.DecodeFloatChannel(scan['data']['ChannelPhi'])[0],
            'ChannelTheta': decodeUtil.DecodeFloatChannel(scan['data']['ChannelTheta']),
            'Distance': [],  # Filled below.
            'Rssi': [],  # Filled below.
            'Properties': decodeUtil.DecodeUint8Channel(scan['data']['PropertiesValues'][0]) if 'PropertiesValues' in scan['data'] else None
        }

        for distChannelRaw in scan['data']['DistValues']:
            curDistData = decodeUtil.DecodeFloatChannel(distChannelRaw)
            scandata['Distance'].append(curDistData)
        for rssiChannelRaw in scan['data']['RssiValues']:
            curRssiData = decodeUtil.DecodeUint16Channel(rssiChannelRaw)
            scandata['Rssi'].append(curRssiData)

        segmentdata.append(scandata)
    return segmentdata

# ===============================================================================


class Receiver:
    """
    Opens the specified port (default is 2115) to listen for incoming MSGPACK formatted segments.
    """

    def __init__(self, host="localhost", port=2115):
        self.connection = connectionHandler.UDPHandler(
            host,
            port,
            # Remote address actually not used since we just want to receive and not send data.
            "localhost",
            # Remote port actually not used since we just want to receive and not send data.
            65535,
            # Buffersize should be large enough to handle multiple layers with many beams.
            100000
        )

    def closeConnection(self):
        """
        Closes the underlying connection.
        """
        del self.connection

    def receiveSegments(self, nbSegments):
        """
        Receives the specified number of segments and returns them as an array along with arrays of corresponding frame
        and segment numbers.
        """
        segments_received = []
        frame_numbers = []
        segment_numbers = []
        for i in range(0, nbSegments):
            bytes_received, _ = self.connection.receiveNewScanSegment()
            if self.connection.hasNoError():
                print(f"Received segment {i}.")
                payload = _verifyAndExtractPayload(bytes_received)
                if payload is not None:
                    (curSegment, curFrameNumber,
                     curSegmentNumber) = parsePayload(payload)
                    segments_received.append(curSegment)
                    frame_numbers.append(curFrameNumber)
                    segment_numbers.append(curSegmentNumber)
                else:
                    print(f"Failed to extract payload from data.", file=sys.stderr)
            else:
                print(
                    f"Failed to receive segment. Error code {self.connection.getLastErrorCode}: {self.connection.lastErrorMessage}", file=sys.stderr)
        return (segments_received, frame_numbers, segment_numbers)
