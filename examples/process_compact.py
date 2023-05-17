#
# Copyright (c) 2023 SICK AG
# SPDX-License-Identifier: MIT
#
# This program receives scan segments in compact format.
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

import numpy as np
import api.compact as CompactApi

if __name__ == "__main__":
    receiver = CompactApi.Receiver(port=2115, host="192.168.0.100")
    (segments, frameNumbers, segmentCounters) = receiver.receiveSegments(200)
    receiver.closeConnection()

    idx = np.where(np.array(segmentCounters) == 2) # find indices of all segments with segmentCounter == 2
    allSeg2 = np.array(segments)[idx] # extract all segments with segmentCounter == 2

    for segment in allSeg2:
        frameNumber = segment["Modules"][0]["FrameNumber"] # extract the frame number of the first module in that segment
        segmentCounter = segment["Modules"][0]["SegmentCounter"] # extract the segment counter of the first module in that segment
        startAngle = segment["Modules"][0]["ThetaStart"][0] # extract the start angle of the first scan of the first module in that segment
        someDistance = segment["Modules"][0]["SegmentData"][0]["Distance"][0][5] # extract the distance measurement of the first echo of the 6th beam of the first scan of the first module in that segment
        print(f"frameNumber = {frameNumber} segmentCounter = {segmentCounter} startAngle = {np.rad2deg(startAngle)} someDistance = {someDistance}")