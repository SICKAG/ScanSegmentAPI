#
# Copyright (c) 2023 SICK AG
# SPDX-License-Identifier: MIT
#
import argparse
import sys

import api.msgpack as MsgpackApi
import api.compact as CompactApi


if __name__ == "__main__":
    # Setup program argument parser.
    argparser = argparse.ArgumentParser(
        description="Command line script tool to receive scan segment data "
                    "either in MSGPACK format or in Compact format. "
                    "Alternatively, it can be used offline by providing msgpack "
                    "files."
    )
    subparsers = argparser.add_subparsers(dest="command")

    receive_parser = subparsers.add_parser(
        "receive", help="Receive data from a remote device.")
    receive_parser.add_argument(
        "format", choices=["msgpack", "compact"], help="Format of received data.")
    receive_parser.add_argument("--host", default="localhost",
                                help="Host address to use for listening. Depending on the network configuration this might differ from 'localhost'. (Default: %(default)s)")
    receive_parser.add_argument("-p", "--port", default=2115, type=int,
                                help="Port at which to listen for incoming data. (Default: %(default)s)")
    receive_parser.add_argument("-n", "--num-segments", dest="num_segments", default=200,
                                type=int, help="Number of segments to receive. (Default: %(default)s)")

    file_parser = subparsers.add_parser(
        "read", help="Read data from a msgpack file.")
    file_parser.add_argument(
        "format", choices=["msgpack", "compact"], help="Format of received data.")
    file_parser.add_argument("-i", "--input", required=True,
                             metavar="FILE", help="File in msgpack format to read.")

    args = argparser.parse_args()
    if (len(sys.argv) == 1):
        argparser.print_help()
        sys.exit(0)

    # Actual program execution.
    if args.command == "read":
        if args.format == "msgpack":
            print(MsgpackApi.parseFromFile(args.input))
        elif args.format == "compact":
            print(CompactApi.parseFromFile(args.input))

    elif args.command == "receive":
        if args.format == "msgpack":
            receiver = MsgpackApi.Receiver(host=args.host, port=args.port)
        elif args.format == "compact":
            receiver = CompactApi.Receiver(host=args.host, port=args.port)

        (segments, frameNumbers, segmentCounters) = receiver.receiveSegments(
            args.num_segments)
        receiver.closeConnection()
