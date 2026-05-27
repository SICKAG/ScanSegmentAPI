# Examples

This directory contains examples for the usage of the ScanSegmentAPI.

* **print_segment_content.py** Example that receives scan segments in Compact format telegram type 1 or MSGPACK format and prints the content of the first five segments with the FrameNumber % 5 = 0 to the console.

* **process_compact.py** Example that shows how to access data fields of segments received in the Compact format telegram type 1 format.

* **process_msgpack.py** Example that shows how to access data fields of segments received in the MSGPACK format.

* **store_segments_json_compact.py** Example that shows how to store segments received in the Compact format telegram type 1 format in a json file.

* **store_segments_json_msgpack.py** Example that shows how to store segments received in the MSGPACK format in a json file.
