#
# Copyright (c) 2023 SICK AG
# SPDX-License-Identifier: MIT
#
# This program receives scan segments in compact format and stores them in
# json format in a file.
#
import numpy as np
import json
from json import JSONEncoder
import api.compact as CompactApi

class SegmentEncoder(JSONEncoder):
    def default(self, obj):
        # modify default behavior for numpy arrays
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return JSONEncoder.default(self, obj)

if __name__ == "__main__":
    receiver = CompactApi.Receiver(port=2115, host="192.168.0.100")
    (segments, frameNumbers, segmentCounters) = receiver.receiveSegments(200)
    receiver.closeConnection()
    with open('segments.json', 'w') as f:
        json.dump(segments, f, cls=SegmentEncoder)