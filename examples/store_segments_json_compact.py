#
# Copyright (c) 2023-2026 SICK AG
# SPDX-License-Identifier: MIT
#
# This program receives scan segments in Compact format and stores them in
# json format in a file.
#
import logging
import numpy as np
import json
from json import JSONEncoder

import scansegmentapi.compact as CompactApi
from scansegmentapi.tcp_handler import TCPHandler
from scansegmentapi.compact_stream_extractor import CompactStreamExtractor
from scansegmentapi.udp_handler import UDPHandler

# Port used for data streaming. Enter the port configured in your device.
PORT = 2115

# If UDP is configured this should be the IP of the receiver.
# If TCP is configured this should be the IP of the SICK device.
IP = "192.168.0.100"

# Select with which transport protocol the data should be received. Select "TCP" or "UDP".
TRANSPORT_PROTOCOL = "UDP"

# Explicitly configure the logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s: %(message)s"
)
logging.getLogger("scansegmentapi").setLevel(logging.INFO)


class SegmentEncoder(JSONEncoder):
    def default(self, obj):
        # modify default behavior for numpy arrays
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return JSONEncoder.default(self, obj)

if __name__ == "__main__":
    if "UDP" == TRANSPORT_PROTOCOL:
        transportLayer = UDPHandler(IP, PORT, 65535)
    else:
        streamExtractor = CompactStreamExtractor()
        # See documentation of the buffer_size argument of the TCP handler for the selection of a
        # suitable value
        transportLayer = TCPHandler(streamExtractor, IP, PORT, 1024)

    receiver = CompactApi.Receiver(transportLayer)
    (segments, frameNumbers, segmentCounters) = receiver.receive_segments(200)
    receiver.close_connection()
    with open('segments.json', 'w') as f:
        json.dump(segments, f, cls=SegmentEncoder)