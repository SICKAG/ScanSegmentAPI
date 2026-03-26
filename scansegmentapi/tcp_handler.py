#
# Copyright (c) 2024 SICK AG
# SPDX-License-Identifier: MIT
#

from queue import Queue
import socket
import time
import logging

from scansegmentapi.transport_handler import TransportHandler


logger = logging.getLogger("scansegmentapi")


class TCPHandler(TransportHandler):
    """This class connects to a TCP server and extracts data packages from the TCP stream.
    In contrast to UDP where one UDP packet contains exactly one data package with measurement
    data (e.g. Compact or MSGPACK data), the measurement data packages arrive in a continuous
    data stream. Therefore the TCPHandler requires a stream_extractor which can assemble one
    measurement data package from the TCP stream. Note that different stream_extractors
    must be used, depending whether Compact or MSGPACK data shall be extracted.
    """

    def __init__(
        self,
        stream_extractor,
        server_ip: str,
        server_port: int,
        buffer_size: int
    ):
        """Opens a TCP connection to a server.

        Args:
            stream_extractor: Extracts data packages from the TCP stream
            server_ip (str): Ip of the server
            server_port (int): Port of the server
            buffer_size (int): The number of bytes that are read from the socket at once.
            The buffer size of the socket.recv method should roughly correspond to the
            size of one scan segment. This avoids many calls of the recv method to
            receive one scan segment (in case of a too small buffer size) and too large
            chunks of data in the memory (in case of a too large buffer size).
        """
        super().__init__()

        self.stream_extractor = stream_extractor
        self.received_segments = Queue(maxsize=0)

        self.buffer: bytes = bytes()
        self.server_ip = server_ip
        self.server_port = server_port
        self.buffer_size = buffer_size
        self.rec_timeout = 3
        self._open_tcp_socket()

    def __del__(self):
        self.client.close()

    def _open_tcp_socket(self):
        self.client = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
        self.client.settimeout(self.rec_timeout)
        logger.info(f"Connecting to TCP:{self.server_ip}:{self.server_port}")
        self.client.connect((self.server_ip, self.server_port))

    def receive_new_scan_segment(self) -> tuple[bytes, str]:
        """Waits on a new scan segment.

        Returns:
            tuple[bytes, str]: Tuple of the received data and the ip address of the server if there
            was no timeout or error. Otherwise an empty byte string and an empty string are
            returned. The server ip is kept for api compatibility reasons. In contrast to UDP there
            is only one server in the TCP connection which is specified when opening the
            connection.
        """
        timeout = time.time() + 5  # timeout of 5 seconds
        try:
            # As long as no segments have been extracted from the stream
            # and the time out has not been reached keep reading from the socket.
            # In the case that multiple measurement data packages are contained in one TCP packet
            # they are added to a queue. With each call of receive_new_scan_segment the first
            # element of the queue is returned and new data is received from the socket only if
            # the queue is empty again.
            while self.received_segments.qsize() == 0 and time.time() < timeout:
                self.no_error_flag = True
                for received_segment in self.stream_extractor.extract_data_packages(
                        self.client.recv(self.buffer_size)):
                    self.received_segments.put(received_segment)

            if time.time() >= timeout:
                logger.warning("No data packages could be found in the data stream within 5 seconds.")
                return bytes(), ""

            return self.received_segments.get(), self.server_ip
        except TimeoutError as e:
            logger.exception(e)
            return bytes(), ""
        except socket.error as error:
            self.no_error_flag = False
            self.last_error_code = error.errno
            self.last_error_message = str(error)
            logger.error(f"Error while receiving TCP data. Error Code: {error.errno}.")
            return bytes(), ""
