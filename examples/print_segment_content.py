#
# Copyright (c) 2023 SICK AG
# SPDX-License-Identifier: MIT
#
#
# This program receives scan segments in compact or
# MSGPACK format and prints the content of all segments with the SegmentCounter = 2 to the console.
#
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

import api.msgpack as MsgpackApi
import api.compact as CompactApi

import numpy as np

###############################################################################################
#                                     CONFIGURATION                                           #
###############################################################################################

# Protocol to be used, select "Compact" or "MSGPACK"
PROTOCOL            = "MSGPACK"

# Select the rinted beam information.
#       False   = Print the distance data of the first beam, layer 0, echo 0
#       True    = Print all captured distance data for each beam such as properties, rssi and
#                 distance values for all echos on layer 0
ALL_MEASURMENT_DATA = True

# Port used for data streaming. Enter the port configured in your device.
PORT                = 2115

# Host IP, this address should match the IP of your receiver.
IP                  = "192.168.0.100"


##############################################################################################


if __name__ == "__main__":
  if "MSGPACK" == PROTOCOL:
    receiver = MsgpackApi.Receiver(port=PORT, host=IP)
  else:
    receiver = CompactApi.Receiver(port=PORT, host=IP)

  (segments, frameNumbers, segmentCounters) = receiver.receiveSegments(12)
  receiver.closeConnection()




# extract all segments with SegmentCounter = 2
idx = np.where(np.array(segmentCounters) == 2)
allSeg2 = np.array(segments)[idx]

# Print all fields with at least one measurement example using MSGPACK protocol
if "MSGPACK" == PROTOCOL:
  LAYER_ID = 1    # The scan layer for which the information in this test are requested (e.g. layer with id 1).
                  # It contains all beams for one elevation angle in the observed segment.
  BEAM     = 0    # The beam index within a layer containing all echos. The beam with index 0 has the azimuth angle ThetaStart.
  ECHO     = 0    # The echo index for which distance and RSSI values are obtained.

  print("Protocol: MSGPACK")
  print("First bracket    = Layer")
  print("Second bracket   = Echo")
  print("Third bracket    = Beam")
  print("-----------------------------------------------------------------------------------")
  for segment in allSeg2:
    print("-----------------------------------------------------------------------------------")

    # Header of a segment
    print(f'TelegramCounter      = {segment["TelegramCounter"]} ')
    print(f'TimestampTransmit    = {segment["TimestampTransmit"]} ')
    print(f'SegmentCounter       = {segment["SegmentCounter"]} ')
    print(f'FrameNumber          = {segment["FrameNumber"]} ')
    print(f'SenderId             = {segment["SenderId"]} ')
    print(f'Availability         = {segment["Availability"]} ')
    print(f'LayerId              = {segment["LayerId"]} ')

    # Find the index of the layer with id LAYER_ID
    layerIndex = segment["LayerId"].index(LAYER_ID)

    # Data per layer, echo and beam
    print(f'TimeStampStart[{layerIndex}]    '
          f'= {segment["SegmentData"][layerIndex]["TimestampStart"]} ')
    print(f'TimeStampStop[{layerIndex}]     '
          f'= {segment["SegmentData"][layerIndex]["TimestampStop"]} ')
    print(f'ThetaStart[{layerIndex}]        '
          f'= {segment["SegmentData"][layerIndex]["ThetaStart"]} ')
    print(f'ThetaStop[{layerIndex}]         '
          f'= {segment["SegmentData"][layerIndex]["ThetaStop"]} ')
    print(f'ScanNumber[{layerIndex}]        '
          f'= {segment["SegmentData"][layerIndex]["ScanNumber"]} ')
    print(f'ModuleId[{layerIndex}]          '
          f'= {segment["SegmentData"][layerIndex]["ModuleID"]} ')
    print(f'ChannelPhi[{layerIndex}]        '
          f'= {segment["SegmentData"][layerIndex]["Phi"]} ')
    print(f'BeamCount[{layerIndex}]         '
          f'= {segment["SegmentData"][layerIndex]["BeamCount"]} ')
    print(f'EchoCount[{layerIndex}]         '
          f'= {segment["SegmentData"][layerIndex]["EchoCount"]} ')

    # All distance data of layer 0
    if ALL_MEASURMENT_DATA:
      print(f'Distance[{layerIndex}]          '
            f'= {segment["SegmentData"][layerIndex]["Distance"]} ')
      print(f'Rssi[{layerIndex}]              '
            f'= {segment["SegmentData"][layerIndex]["Rssi"]} ')
      print(f'PropertyValues[{layerIndex}]    '
            f'= {segment["SegmentData"][layerIndex]["Properties"]} ')
      print(f'ChannelTheta[{layerIndex}][{BEAM}]   '
            f'= {segment["SegmentData"][layerIndex]["ChannelTheta"]} ')

    # Single beam only
    else:
      print(f'Distance[{layerIndex}][{ECHO}][{BEAM}]    '
            f'= {segment["SegmentData"][layerIndex]["Distance"][ECHO][BEAM]} ')
      print(f'Rssi[{layerIndex}][{ECHO}][{BEAM}]        '
            f'= {segment["SegmentData"][layerIndex]["Rssi"][ECHO][BEAM]} ')
      print(f'PropertyValues[{layerIndex}][{BEAM}] '
            f'= {segment["SegmentData"][layerIndex]["Properties"][BEAM]} ')
      print(f'ChannelTheta[{layerIndex}][{BEAM}]   '
            f'= {segment["SegmentData"][layerIndex]["ChannelTheta"][BEAM]} ')

    print("-----------------------------------------------------------------------------------")

# Print all fields with at least one measurement example using Compact protocol
else:
  MODULE = 0     # The number of the desired module. A module serves to group data with either different physical origins or different angle resolutions.
  LAYER  = 0     # Layer index within a module, contains all beams of one layer and one module.
  BEAM   = 0     # The beam index within a layer. The beam with index 0 has the azimuth angle ThetaStart.
  ECHO   = 0     # The echo index for which distance and RSSI values are obtained.

  print("Protocol: Compact")
  print("First bracket    = Module")
  print("Second bracket   = Scan")
  print("Third bracket    = Echo")
  print("Fourth bracket   = Beam")
  print("-----------------------------------------------------------------------------------")
  for segment in allSeg2:
    print("-----------------------------------------------------------------------------------")

    # Header of the segment
    print(f'CommandId                = {segment["CommandId"]} ')
    print(f'TelegramCounter          = {segment["TelegramCounter"]} ')
    print(f'TimeStampTransmit        = {segment["TimestampTransmit"]} ')
    print(f'TelegramVersion          = {segment["Version"]} \n')

    # Meta data for module 0 of the current segment.
    print(f'SegmentCounter[{MODULE}]        '
              f'= {segment["Modules"][MODULE]["SegmentCounter"]} ')
    print(f'FrameNumber[{MODULE}]           '
              f'= {segment["Modules"][MODULE]["FrameNumber"]} ')
    print(f'SenderId[{MODULE}]              '
              f'= {segment["Modules"][MODULE]["SenderId"]} ')
    print(f'NumberOfLinesInModule[{MODULE}] '
              f'= {segment["Modules"][MODULE]["NumberOfLinesInModule"]} ')
    print(f'NumberOfBeamsPerScan[{MODULE}]  '
              f'= {segment["Modules"][MODULE]["NumberOfBeamsPerScan"]} ')
    print(f'NumberOfEchosPerBeam[{MODULE}]  '
              f'= {segment["Modules"][MODULE]["NumberOfEchosPerBeam"]} ')
    print(f'TimeStampStart[{MODULE}][{LAYER}]     '
              f'= {segment["Modules"][MODULE]["TimestampStart"][LAYER]} ')
    print(f'TimeStampStop[{MODULE}][{LAYER}]      '
              f'= {segment["Modules"][MODULE]["TimestampStop"][LAYER]} ')
    print(f'Phi[{MODULE}][{LAYER}]                '
              f'= {segment["Modules"][MODULE]["Phi"][LAYER]} ')
    print(f'ThetaStart[{MODULE}][{LAYER}]         '
              f'= {segment["Modules"][MODULE]["ThetaStart"][LAYER]} ')
    print(f'ThetaStop[{MODULE}][{LAYER}]          '
              f'= {segment["Modules"][MODULE]["ThetaStop"][LAYER]} ')
    print(f'DataContentEchos[{MODULE}]      '
              f'= {segment["Modules"][MODULE]["DataContentEchos"]} ')
    print(f'DataContentBeams[{MODULE}]      '
              f'= {segment["Modules"][MODULE]["DataContentBeams"]} ')

    # Beam data of the selected layer of the selected module

    # All distance data of the selected layer of the selected module
    if ALL_MEASURMENT_DATA:
      print(f'Distance[{MODULE}][{LAYER}]           '
            f'= {segment["Modules"][MODULE]["SegmentData"][LAYER]["Distance"]} ')
      print(f'Rssi[{MODULE}][{LAYER}]               '
            f'= {segment["Modules"][MODULE]["SegmentData"][LAYER]["Rssi"]} ')
      print(f'PropertyValues[{MODULE}][{LAYER}]     '
            f'= {segment["Modules"][MODULE]["SegmentData"][LAYER]["Properties"]} ')
      print(f'ChannelTheta[{MODULE}][{LAYER}]       '
            f'= {segment["Modules"][MODULE]["SegmentData"][LAYER]["ChannelTheta"]} ')

    # Single beam of the selected layer of the selected module
    else:
      print(f'Distance[{MODULE}][{LAYER}][{ECHO}][{BEAM}]     '
            f'= {segment["Modules"][MODULE]["SegmentData"][LAYER]["Distance"][ECHO][BEAM]}')
      print(f'Rssi[{MODULE}][{LAYER}][{ECHO}][{BEAM}]         '
            f'= {segment["Modules"][MODULE]["SegmentData"][LAYER]["Rssi"][ECHO][BEAM]} ')
      print(f'PropertyValues[{MODULE}][{LAYER}][{BEAM}]  '
            f'= {segment["Modules"][MODULE]["SegmentData"][LAYER]["Properties"][BEAM]} ')
      print(f'ChannelTheta[{MODULE}][{LAYER}][{BEAM}]    '
            f'= {segment["Modules"][MODULE]["SegmentData"][LAYER]["ChannelTheta"][BEAM]} ')

    print("-----------------------------------------------------------------------------------")