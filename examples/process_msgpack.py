#
# Copyright (c) 2023 SICK AG
# SPDX-License-Identifier: MIT
#
# This program receives scan segments in msgpack format.
# The received data consists of a list of segments where
# each segment is represented as a dictionary, a list
# with frame counters and a list with segment counters
# which have the same length as the list of segments.
# This data is processed in the example below as follows:
#
# All segments with the segment counter 2 are extracted.
# For all these segments the frame number and the segment counter
# and the start angle of the first scan are retrieved and printed.


import numpy as np
import api.msgpack as MSGPACKApi

if __name__ == "__main__":
    receiver = MSGPACKApi.Receiver(port=2115, host="192.168.0.100")
    (segments, frameNumbers, segmentCounters) = receiver.receiveSegments(200)
    receiver.closeConnection()

    idx = np.where(np.array(segmentCounters) == 2) # find indices of all segments with segmentCounter == 2
    allSeg2 = np.array(segments)[idx] # extract all segments with segmentCounter == 2

    for segment in allSeg2:
        frameNumber = segment["FrameNumber"] # extract the frame number of that segment
        segmentCounter = segment["SegmentCounter"] # extract the segment counter of that segment
        startAngle = segment["SegmentData"][0]["ThetaStart"] # extract the start angle of the first scan in that segment
        someDistance = segment["SegmentData"][0]["Distance"][0][5] # extract the distance measurement of the first echo of the 6th beam of the first scan in that segment
        print(f"frameNumber = {frameNumber} segmentCounter = {segmentCounter} startAngle = {np.rad2deg(startAngle)} someDistance = {someDistance}")