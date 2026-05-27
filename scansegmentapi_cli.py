#
# Copyright (c) 2023-2026 SICK AG
# SPDX-License-Identifier: MIT
#
import argparse
import logging
import sys

import scansegmentapi.msgpack as MsgpackApi
import scansegmentapi.compact as CompactApi


from scansegmentapi import msgpack_stream_extractor
from scansegmentapi import compact_stream_extractor
from scansegmentapi.tcp_handler import TCPHandler
from scansegmentapi.udp_handler import UDPHandler


if __name__ == "__main__":
    # Setup program argument parser.
    argparser = argparse.ArgumentParser(
        description="Command line script tool to receive scan segment data "
                    "either in MSGPACK or in Compact format via either UDP or TCP. "
                    "Alternatively, it can be used offline by providing .msgpack "
                    "or .compact files."
    )
    subparsers = argparser.add_subparsers(dest="command")

    receive_parser = subparsers.add_parser(
        "receive", help="Receive data from a remote device.")
    receive_parser.add_argument(
        "format", choices=["msgpack", "compact"], help="Format of received data.")
    receive_parser.add_argument("--ip", default="localhost",
                                help="If UDP is selected as the protocol the IP address of the "
                                "network adapter of the client PC on which to receive the incoming "
                                "data has to be given."
                                "Depending on the network configuration this might differ from 'localhost'. "
                                "If TCP is selected as the protocol the IP address of the sensor has to be given. (Default: %(default)s)")
    receive_parser.add_argument("-p", "--port", default=2115, type=int,
                                help="If UDP is selected as the protocol the port at which to listen for incoming data has to be given. "
                                " If TCP is selected as the protocol the port on which the sensor waits for new connections has to be given. "
                                "(Default: %(default)s)")
    receive_parser.add_argument("-n", "--num-segments", dest="num_segments", default=200,
                                type=int, help="Number of segments to receive. (Default: %(default)s)")
    receive_parser.add_argument(
        "--protocol",
        default="udp",
        choices=["udp", "tcp"],
        help="Transport protocol to use for listening. Chose between 'udp' and 'tcp'. (Default: %(default)s)",
    )

    file_parser = subparsers.add_parser(
        "read", help="Read data from a .msgpack file.")
    file_parser.add_argument(
        "format", choices=["msgpack", "compact"], help="Format of received data.")
    file_parser.add_argument("-i", "--input", required=True,
                             metavar="FILE", help="File in MSGPACK format to read.")

    args = argparser.parse_args()
    if len(sys.argv) == 1:
        argparser.print_help()
        sys.exit(0)

    logging.getLogger("scansegmentapi").setLevel(logging.INFO)

    # Actual program execution.
    if args.command == "read":
        if args.format == "msgpack":
            print(MsgpackApi.parse_from_file(args.input))
        elif args.format == "compact":
            print(CompactApi.parse_from_file(args.input))

    elif args.command == "receive":
        if args.protocol == "tcp":
            if args.format == "msgpack":
                streamExtractor = msgpack_stream_extractor.MsgpackStreamExtractor()
            else:
                streamExtractor = compact_stream_extractor.CompactStreamExtractor()
            transportProtocol = TCPHandler(streamExtractor, args.ip, args.port, 1024)
        elif args.protocol == "udp":
            transportProtocol = UDPHandler(args.ip, args.port, 65535)
        else:
            print("Invalid transport protocol selected '{}'", args.protocol)
            sys.exit(1)

        if args.format == "msgpack":
            receiver = MsgpackApi.Receiver(transportProtocol)
        elif args.format == "compact":
            receiver = CompactApi.Receiver(transportProtocol)

        (segments, frameNumbers, segmentCounters) = receiver.receive_segments(
            args.num_segments)
        receiver.close_connection()
