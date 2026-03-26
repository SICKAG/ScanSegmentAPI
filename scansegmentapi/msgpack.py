#
# Copyright (c) 2023-2024 SICK AG
# SPDX-License-Identifier: MIT
#

import sys
import zlib
import logging

from scansegmentapi import msgpack_util
from scansegmentapi import decode_util


logger = logging.getLogger("scansegmentapi")


def parse_from_file(filename):
    """
    Reads a Msgpack formatted binary file and parses its content to a dictionary.
    """
    with open(filename, "rb") as f:
        logger.info(f"Parsing {filename}...")
        byte_data = f.read()
        return parse_payload(byte_data)


def parse_payload(payload):
    """
    Parses the given payload as byte array into a dictionary.
    Along with the dictionary the frame number and segment number of the
    parsed segment are returned.
    """
    data_dict = msgpack_util.unpack_msgpack_and_replace_integer_keywords(payload)

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
        'SegmentData': _extract_segment_data(data_dict['data']['SegmentData'])
    }
    return (segment, segment['FrameNumber'], segment['SegmentCounter'])


def _verify_and_extract_payload(data):
    """
    Checks if the payload contained in the given byte array is complete.
    The extracted payload is returned if it is the case. Otherwise None is returned.
    """
    bytes_frame_start = data[0:4]
    bytes_payload_length = data[4:8]
    bytes_payload = data[8:-4]
    # CRC is computed over payload only without the frame start and length bytes.
    bytes_crc = data[-4:]

    # Check if frame header is included.
    if b'\x02\x02\x02\x02' != bytes_frame_start:
        logger.warning(
            "Missing start of frame sequence [0x02 0x02 0x02 0x02].")
        return None

    # Check if received payload length matches expected one.
    expected_payload_length = int.from_bytes(bytes_payload_length, 'little')
    if expected_payload_length != len(bytes_payload):
        logger.warning(
            f"Actual length of payload and expected length do not match. \
            Expected {expected_payload_length} bytes, got {len(bytes_payload)}.")
        return None

    # Apply CRC.
    expected_crc = int.from_bytes(bytes_crc, 'little')
    computed_crc = zlib.crc32(bytes_payload)
    if expected_crc != computed_crc:
        logger.warning(
            "CRC failed. Expected {expected_crc}, got {computed_crc}.")
        return None

    return bytes_payload


def _extract_segment_data(segment_data_raw):
    """
    Extracts the actual data value contained in the segment (namely distances,
    RSSIs and properties) along with the metadata of each single layer.
    Returned is an array of dictionaries where each array item corresponds to a single layer.
    """
    segment_data = []
    for scan in segment_data_raw:
        scan_data = {
            'TimestampStart': scan['data']['TimestampStart'],
            'TimestampStop': scan['data']['TimestampStop'],
            'ThetaStart': scan['data']['ThetaStart'],
            'ThetaStop': scan['data']['ThetaStop'],
            'ScanNumber': scan['data']['ScanNumber'],
            'ModuleID': scan['data']['ModuleID'],
            'BeamCount': scan['data']['BeamCount'],
            'EchoCount': scan['data']['EchoCount'],
            # Phi is constant for a single layer so we just select the very first one.
            'Phi': decode_util.decode_float_channel(scan['data']['ChannelPhi'])[0],
            'ChannelTheta': decode_util.decode_float_channel(scan['data']['ChannelTheta']),
            'Distance': [],  # Filled below.
            'Rssi': [],  # Filled below.
            'Properties': decode_util.decode_uint8_channel(
                scan['data']['PropertiesValues'][0]) if 'PropertiesValues' in scan['data'] else None
        }

        for dist_channel_raw in scan['data']['DistValues']:
            cur_dist_data = decode_util.decode_float_channel(dist_channel_raw)
            scan_data['Distance'].append(cur_dist_data)
        for rssi_channel_raw in scan['data']['RssiValues']:
            cur_rssi_data = decode_util.decode_uint16_channel(rssi_channel_raw)
            scan_data['Rssi'].append(cur_rssi_data)

        segment_data.append(scan_data)
    return segment_data

# ===============================================================================


class Receiver:
    """
    Receives data from the transport layer and parses the data using the MSGPACK format.
    """

    def __init__(self, transport_layer):
        self.transport_layer = transport_layer

    def close_connection(self):
        """
        Closes the underlying connection.
        """
        del self.transport_layer

    def receive_segments(self, nb_segments):
        """
        Receives the specified number of segments and returns them as an array along with
        arrays of corresponding frame and segment numbers.
        """
        segments_received = []
        frame_numbers = []
        segment_numbers = []
        for i in range(0, nb_segments):
            bytes_received, _ = self.transport_layer.receive_new_scan_segment()
            if self.transport_layer.has_no_error():
                logger.info(f"Received segment {i}.")
                payload = _verify_and_extract_payload(bytes_received)
                if payload is not None:
                    (cur_segment, cur_frame_number,
                     cur_segment_number) = parse_payload(payload)
                    segments_received.append(cur_segment)
                    frame_numbers.append(cur_frame_number)
                    segment_numbers.append(cur_segment_number)
                else:
                    logger.warning("Failed to extract payload from data.")
            else:
                logger.error(
                    f"Failed to receive segment. Error code \
                    {self.transport_layer.get_last_error_code()}: \
                    {self.transport_layer.last_error_message}")
        return (segments_received, frame_numbers, segment_numbers)
