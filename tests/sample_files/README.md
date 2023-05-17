# Disclaimer

The sample files located inside `tests/sample_files` are mainly used for the unit tests and have been created artificially. They do not contain real sensor data. Nonetheless, they can be used to test your own parser implementations for MSGPACK and Compact. Please keep in mind, that a successful parsing of the sample files does not guarantee a valid parser implementation for the data formats with all their features. It is advisable to test the parser on real sensor data as well.

# Sample files

The files located in this directory are sample files mainly used by the unit tests. Each file contains data of a single
segment either serialized to MSGPACK (`*.msgpack`) or Compact (`*.compact`) format respectively. It should be noted that
the MSGPACK files contain the plain payload without framing (STX bytes) and CRC. But for Compact files the framing is
considered to be part of the payload as the CRC also includes the STX bytes. Thus in contrast to the MSGPACK files
Compact files always start with four STX bytes and end with the CRC.

## sample.compact / sample.msgpack

These files include an arificially generated segment with the following content:

* Single segment containing two scans
* Segment number is 666
* Frame number is 999
* Availability is true/1
* Telegram counter is 333
* Timestamp transmit is 444
* Sender id is 555
* Both scans have 10 beams at 2 echos respectively
* Scan numbers are 22 for the first and 11 for the second scan
* Module ids are 54 for the first and 56 for the second scan
* The first scan covers a range of 0 to 9° with 1° resolution whereas distances for all beams are 123.456 and RSSIs are 0.321 (which translates to 21036 in uint16 format)
* The second scan covers a range of 90° to 99° with 1° resolution whereas distances for all beams are 456.123 and RSSIs are 0.678 (which translates to 44432 in uint16 format)
* Properties are undefined for both scans as well as timestamps and elevation angles.

## sample_30deg.compact / sample_30deg.msgpack

The files are more close to real-life data acquired using a multiScan device. The contents are similar to sample.compact
and sample.msgpack with the following difference:

* Single segment containing 16 scans
* Each scan has 30 beams at 3 echos respectively
* Reflector bit is set for each beam
* Scan numbers are 1, 2, ..., 16
* Module ids are 0

### Remarks

* Since the Compact format stores distance values as uint16 the original float which are present in the MSGPACK format values are clipped.
* In Compact format azimuth angle values (theta) are also represented as uint16 values and scaled to match the full possible angle range. The API maps them back to float values including some clipping due to the loss of precision.