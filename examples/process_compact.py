#
# Copyright (c) 2023-2026 SICK AG
# SPDX-License-Identifier: MIT
#
# This program receives scan segments in Compact format.
# The received data consists of a list of segments where
# each segment is represented as a dictionary, a list
# with frame counters and a list with segment counters
# which have the same length as the list of segments.
# This data is processed in the example below.
#
# All segments with the segment counter 2 are extracted.
# For all these segments the frame number and the segment
# counter for the first module and the start angle of the
# first scan of the first module are retrieved and printed.

import logging
import numpy as np

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

    # find indices of all segments with frameNumber % 5 == 0
    idx = np.where(np.array(frameNumbers) % 5 == 0)
    segmentsFrameNumberMod5 = np.array(segments)[idx][:5]  # extract the first 5 segments with frameNumber % 5 == 0

    for segment in segmentsFrameNumberMod5:
        # extract the frame number of the first module in that segment
        frameNumber = segment["Modules"][0]["FrameNumber"]
        # extract the segment counter of the first module in that segment
        segmentCounter = segment["Modules"][0]["SegmentCounter"]
        # extract the start angle of the first scan of the first module in that segment
        startAngle = segment["Modules"][0]["ThetaStart"][0]
        # extract the distance measurement of the first echo of the 6th beam of the first scan of the first module in that segment
        someDistance = segment["Modules"][0]["SegmentData"][0]["Distance"][0][5]
        print(
            f"frameNumber = {frameNumber} segmentCounter = {segmentCounter} startAngle = {np.rad2deg(startAngle)} someDistance = {someDistance}")
