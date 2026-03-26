#
# Copyright (c) 2023-2024 SICK AG
# SPDX-License-Identifier: MIT
#
import struct
import sys
from typing import Any
import zlib
import numpy as np
import logging


logger = logging.getLogger("scansegmentapi")


def parse_from_file(filename):
    """
    Reads a Compact formatted binary file and parses its content to a dictionary.
    """
    with open(filename, "rb") as f:
        logger.info(f"Parsing {filename}...")
        byte_data = f.read()
        payload = _verify_and_extract_payload(byte_data)
        return parse_payload(payload)


def parse_payload(payload):
    """
    Parses a Compact formatted byte array into a dictionary.
    """
    #
    # In the Compact format the payload consists of a header which is 32 bytes long and zero or
    # more modules of variable length depending on the number of layers in the segment.
    # The header stores the size of the very first module whereas each module stores the size of
    # the following module in its metadata.
    #
    # | Header | Module 1 | Module 2 | ...
    # 0       32          X          Y
    #
    # With X = size of module 1 + 32
    #      Y = size of module 2 + size of module 1 + 32
    #
    result: dict[str, Any] = {
        "Modules": []
    }
    (header, next_module_size) = _read_header(payload)
    last_module_size = 0

    result.update(header)

    offset = 32  # 32 bytes header size
    while next_module_size > 0:
        last_module_size = next_module_size
        (module_data, next_module_size) = _read_next_module(payload, offset)
        if module_data is None:
            logger.warning("Failed to read module data.")
            return None
        result["Modules"].append(module_data)
        offset += last_module_size

    return result


def _verify_and_extract_payload(data):
    """
    Checks for the STX byte sequence and applies CRC.
    """
    bytes_frame_start = data[0:4]
    bytes_crc = data[-4:]
    # CRC is computed over whole data including the frame start bytes.
    bytes_payload = data[0:-4]

    # Check if frame header is included.
    if b'\x02\x02\x02\x02' != bytes_frame_start:
        logger.warning(
            "Missing start of frame sequence [0x02 0x02 0x02 0x02].")
        return None

    # Apply CRC
    expected_crc = int.from_bytes(bytes_crc, 'little')
    computed_crc = zlib.crc32(bytes_payload)
    if expected_crc != computed_crc:
        logger.warning(
            f"CRC failed. Expected {expected_crc}, got {computed_crc}.")
        return None

    return bytes_payload


def _read_header(data):
    """
    Reads the header data from the given Compact formatted data array.
    """
    # The header itself is 32 bytes long.
    #
    # | <STX><STX><STX><STX> | CommandId | TelegramCounter | TimestampTransmit | Version | ModuleSize |
    # 0                      4           8                 16                  24        28           32
    #
    command_id, _ = _read_uint32(data, 4)
    telegram_counter, _ = _read_uint64(data, 8)
    timestamp_transmit, _ = _read_uint64(data, 16)
    version, _ = _read_uint32(data, 24)
    next_module_size, _ = _read_uint32(data, 28)

    header = {
        'CommandId': command_id,
        'TelegramCounter': telegram_counter,
        'TimestampTransmit': timestamp_transmit,
        'Version': version
    }
    return (header, next_module_size)


def _read_next_module(data, offset):
    """
    Reads the module at the given offset.
    """
    #
    # A module always consists of two blocks of variable lengths.
    # The first block contains the metadata describing the actual contents of
    # the module (beam data) which is stored in the second block.
    #
    # | STX | Header | Module 1 | Module 2 | ...
    # 0     4        32         X          Y
    #                |          |          +---------------------------------+
    #                |          |                                            |
    #                |          +----------------+                           |
    #                |                           |                           |
    #            ... | Metadata 1 | Beam data 1 | Metadata 2 | Beam data 2 | ...
    #
    metadata, next_module_size, offset = _read_meta_data(data, offset)
    beam_data = _read_beam_data(data, metadata, offset)

    # Merge metadata and beam data into a single dictionary.
    module_data = {}
    module_data.update(metadata)
    if beam_data is not None:
        module_data.update(beam_data)

    return (module_data, next_module_size)


def _read_meta_data(data, offset):
    # The metadata itself has variable length depending on the number layers which is also
    # encoded in this block.
    # For example consider a block starting at offset X:
    #
    # | SegmentCounter | FrameNumber | SenderId | NumLayers | BeamCount | EchoCount |
    # X               X+8           X+16       X+20        X+24        X+28        X+32
    #
    # The first portion of the metadata has a fixed length of 32 byte.
    # Afterwards array data is included:
    #
    # | TimestampStart | TimestampStop    | Phi             | ThetaStart       | ThetaStop      | DistanceScalingFactor
    # X+32        +(NumLayers*8)     +(NumLayers*8)    +(NumLayers*4)     +(NumLayers*4)   +(NumLayers*4)  + 4
    #
    # In sum this block stops at byte offset
    # Y = (X+32)+(2*NumLayers*8)+(3*NumLayers*4)+4 = (X+32)+(28*NumLayers)+4
    # Finally, the block is concluded with a fixed size portion again:
    #
    # | NextModuleSize | Availability | DataContentEchos | DataContentBeams | Reserved |
    # Y               Y+4            Y+5                Y+6                Y+7        Y+8
    #
    segment_counter, offset = _read_uint64(data, offset)
    frame_number, offset = _read_uint64(data, offset)
    sender_id, offset = _read_uint32(data, offset)
    num_layers, offset = _read_uint32(data, offset)
    beam_count, offset = _read_uint32(data, offset)
    echo_count, offset = _read_uint32(data, offset)
    timestamp_start, offset = _read_uint64_array(data, num_layers, offset)
    timestamp_stop, offset = _read_uint64_array(data, num_layers, offset)
    phi, offset = _read_float32_array(data, num_layers, offset)
    theta_start, offset = _read_float32_array(data, num_layers, offset)
    theta_stop, offset = _read_float32_array(data, num_layers, offset)
    distance_scaling_factor, offset = _read_float32(data, offset)
    next_module_size, offset = _read_uint32(data, offset)
    availability, offset = _read_uint8(data, offset)
    data_content_echos, offset = _read_uint8(data, offset)
    data_content_beams, offset = _read_uint8(data, offset)
    reserved, offset = _read_uint8(data, offset)

    # Bit mask to be applied on the 'data_content' variables.
    mask_distance_available = 0x01
    mask_rssi_available = 0x02
    mask_properties_available = 0x01
    mask_theta_available = 0x02

    meta_data = {
        "SegmentCounter": segment_counter,
        "FrameNumber": frame_number,
        "SenderId": sender_id,
        "NumberOfLinesInModule": num_layers,
        "NumberOfBeamsPerScan": beam_count,
        "NumberOfEchosPerBeam": echo_count,
        "TimestampStart": timestamp_start,
        "TimestampStop": timestamp_stop,
        "Phi": phi,
        "ThetaStart": theta_start,
        "ThetaStop": theta_stop,
        "DistanceScalingFactor": distance_scaling_factor,
        "Availability": availability,
        "DataContentEchos": data_content_echos,
        "DataContentBeams": data_content_beams,
        "HasDistance": ((data_content_echos & mask_distance_available) != 0),
        "HasRssi": ((data_content_echos & mask_rssi_available) != 0),
        "HasProperties": ((data_content_beams & mask_properties_available) != 0),
        "HasTheta": ((data_content_beams & mask_theta_available) != 0)

    }
    return (meta_data, next_module_size, offset)


def _read_beam_data(data, metadata, offset):
    #
    # If all channels are enabled, the beam data always has the following structure:
    #
    # | dist_00 | rssi_00 | ... | dist_0n | rssi_0n | theta_0 | prop_0 |        <- Data of beam 0
    # | dist_10 | rssi_10 | ... | dist_1n | rssi_1n | theta_1 | prop_1 |        <- Data of beam 1
    #   ...
    # | dist_m0 | rssi_m0 | ... | dist_mn | rssi_mn | theta_m | prop_m |        <- Data of beam m
    #
    # whereas dist_mn and rssi_mn are the distance and rssi values respectively for
    # beam m and echo n. theta_m and prop_m are theta and property values of beam m respectively.
    # Only distance values are required. More than one echos are optional as well as existence of
    # rssi, theta and property data.
    # Therefore the bare minimum a segment in the Compact format can have is:
    #
    # | dist_00 | dist_10 | ... | dist_m0 |

    # The line above has one single distance value for each
    # of the m beams (each with only one echo).
    #
    num_layers = metadata["NumberOfLinesInModule"]
    num_echos = metadata["NumberOfEchosPerBeam"]
    num_beams = metadata["NumberOfBeamsPerScan"]

    # Prepare result object by creating an array of empty, zero-initialized dictionaries,
    # one for each layer.
    result = [{
        # Matrix of size num_echos * num_beams.
        'Rssi': [np.zeros(num_beams) for n in range(num_echos)],
        # Matrix of size num_echos * num_beams.
        'Distance': [np.zeros(num_beams) for n in range(num_echos)],
        'ChannelTheta': np.zeros(num_beams),
        'Properties': np.zeros(num_beams)
    } for n in range(num_layers)]

    if not metadata["HasDistance"]:
        logger.warning(
            f"Failed to read beam data from module. \
                No distance data available. Metadata: {metadata}")
        return None

    # Format string used when data is unpacked.
    # For example for three echos, when all data channels are active the
    # result will be:
    # '<HHHHHHBH' (6 x 16-bit values = 3 x distance + 3 x rssi, 1 x property, 1 x theta
    # encoding the property all in little endian format marked by '<').
    # See https://docs.python.org/3/library/struct.html for further information.
    format_string = "<" \
        + num_echos * "H" \
        + (num_echos * "H" if metadata["HasRssi"] else "") \
        + ("B" if metadata["HasProperties"] else "") \
        + ("H" if metadata["HasTheta"] else "")

    # Data is extracted beam by beam from payload whereas all values related to a single beam are
    # parsed at once in each iteration and stored in a tuple. Each beam value
    # (distance, rssi, theta and property) are stored at a distinct index in this tuple:
    tuple_indices_distance = [0] * num_echos
    tuple_indices_rssi = [0] * num_echos
    tuple_index_theta = 0
    tuple_index_property = 0
    tuple_index = 0
    for echo_idx in range(num_echos):
        tuple_indices_distance[echo_idx] = tuple_index
        tuple_index += 1
        if metadata["HasRssi"]:
            tuple_indices_rssi[echo_idx] = tuple_index
            tuple_index += 1
    if metadata["HasProperties"]:
        tuple_index_property = tuple_index
        tuple_index += 1
    if metadata["HasTheta"]:
        tuple_index_theta = tuple_index

    # Extract data from payload.
    for beam_idx in range(num_beams):
        for layer_idx in range(num_layers):
            # Extract all beam values at once (as tuple) according to declared format string.
            beam_data = struct.unpack_from(format_string, data, offset)
            offset += struct.calcsize(format_string)
            for echo_idx in range(num_echos):
                tuple_index_distance = tuple_indices_distance[echo_idx]
                tuple_index_rssi = tuple_indices_rssi[echo_idx]
                result[layer_idx]['Distance'][echo_idx][beam_idx] = \
                    beam_data[tuple_index_distance] * metadata["DistanceScalingFactor"]
                result[layer_idx]['Rssi'][echo_idx][beam_idx] = \
                    beam_data[tuple_index_rssi] if metadata["HasRssi"] else None
            # Theta must be converted from simple unsigned int to actual angle in radians
            # according to: angleUINT = floor(angleRAD * 5215 + 16384)
            result[layer_idx]['ChannelTheta'][beam_idx] = (
                beam_data[tuple_index_theta] - 16384) / 5215.0 if metadata["HasTheta"] else None
            result[layer_idx]['Properties'][beam_idx] = \
                beam_data[tuple_index_property] if metadata["HasProperties"] else None

    return {'SegmentData': result}


def _read_uint8(data, offset):
    """
    Reads one byte as integer at the given offset.
    Additionally the position of the byte following the integer is returned.
    """
    return _read_uint(data, offset, 1)


def _read_uint32(data, offset):
    """
    Reads four bytes as integer at the given offset.
    Additionally the position of the byte following the integer is returned.
    """
    return _read_uint(data, offset, 4)


def _read_uint64(data, offset):
    """
    Reads eight bytes as integer at the given offset.
    Additionally the position of the byte following the integer is returned.
    """
    return _read_uint(data, offset, 8)


def _read_uint(data, offset, value_size):
    """
    Reads an integer of the given size at the specified offset.
    Additionally the position of the byte following the integer is returned.
    """
    value = int.from_bytes(
        data[offset:offset+value_size], byteorder='little', signed=False)
    return (value, offset + value_size)


def _read_float32(data, offset):
    """
    Reads four bytes as float at the given offset.
    Additionally the position of the byte following the float is returned.
    """
    value_size = 4
    value = struct.unpack('<f', data[offset:offset+value_size])
    return (value[0], offset + value_size)


def _read_uint64_array(data, num_elements, offset):
    """
    Reads num_elements * 8 bytes as an unsigned integer array at the given offset.
    Additionally the position of the byte following the array is returned.
    """
    value_size = num_elements * 8
    array_data = struct.unpack_from('<'+f"{num_elements}"+'Q', data, offset)
    return (np.array(array_data), offset + value_size)


def _read_float32_array(data, num_elements, offset):
    """
    Reads num_elements * 4 bytes as a float array at the given offset.
    Additionally the position of the byte following the array is returned.
    """
    value_size = num_elements * 4
    array_data = struct.unpack_from('<'+f"{num_elements}"+'f', data, offset)
    return (np.array(array_data), offset + value_size)

# ===============================================================================


class Receiver:
    """
    Receives data from the transport layer and parses the data using the Compact format.
    """

    def __init__(self, transport_layer):
        self.transport_layer = transport_layer

    def close_connection(self):
        """
        Closes the underlying connection.
        """
        del self.transport_layer

    # receive the specified number of segments
    def receive_segments(self, nb_segments):
        """
        Receives the specified number of segments and returns them as an array along with arrays
        of corresponding frame and segment numbers.
        """
        segments_received = []
        frame_numbers = []
        segment_numbers = []

        for i in range(0, nb_segments):
            bytes_received, _ = self.transport_layer.receive_new_scan_segment()
            if self.transport_layer.has_no_error():
                logger.info(f"Received segment {i}.")
                payload = _verify_and_extract_payload(bytes_received)
                if payload is None:
                    logger.warning("Failed to extract payload from data.")
                    continue
                segment_data = parse_payload(payload)
                if segment_data is not None:
                    segments_received.append(segment_data)
                    frame_numbers.append(segment_data["Modules"][0]['FrameNumber'])
                    segment_numbers.append(
                        segment_data["Modules"][0]['SegmentCounter'])
                else:
                    logger.warning("Failed to parse segment data from payload.")
            else:
                logger.error(
                    f"Failed to receive segment. Error code \
                    {self.transport_layer.get_last_error_code()}: \
                    {self.transport_layer.last_error_message}")

        return (segments_received, frame_numbers, segment_numbers)
