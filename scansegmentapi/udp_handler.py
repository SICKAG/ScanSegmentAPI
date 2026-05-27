#
# Copyright (c) 2024 SICK AG
# SPDX-License-Identifier: MIT
#

import socket
import logging

from scansegmentapi.transport_handler import TransportHandler


logger = logging.getLogger("scansegmentapi")


class UDPHandler(TransportHandler):
    """This class receives UDP packets which arrive from a specified port.
    """

    def __init__(
        self,
        local_address: str,
        local_port: int,
        buffer_size: int
    ):
        """Opens a new socket.

        Args:
            local_address (str): IP address of the receiver
            local_port (int): Port to listen on
            buffer_size (int): Size of the receive buffer
        """
        super().__init__()

        self.local_ip = local_address
        self.local_port = local_port
        self.buffer_size = buffer_size
        self.rec_timeout = 3

        self._open_udp_socket()

    def __del__(self):
        """Closes the socket.
        """
        self.client.close()

    def _open_udp_socket(self):
        """Opens the socket and binds it to the configured port
        """
        self.client = socket.socket(
            family=socket.AF_INET, type=socket.SOCK_DGRAM)

        self.client.bind((self.local_ip, self.local_port))

        self.client.settimeout(self.rec_timeout)

    def receive_new_scan_segment(self) -> tuple[bytes, str]:
        """Waits on a new scan segment.

        Returns:
            tuple[bytes, str]: Tuple of the received data and the ip address of the sender
            to identify which sensor sent the data
        """
        try:
            self.no_error_flag = True
            data, sender_address = self.client.recvfrom(self.buffer_size)
            self.counter += 1
            return data, sender_address
        except TimeoutError as e:
            logger.exception(e)
            return bytes(), ""
        except socket.error as error:
            # print error code
            self.no_error_flag = False
            self.last_error_code = error.errno
            self.last_error_message = str(error)
            logger.exception(error)
            return bytes(), ""

    def close(self):
        """Does not apply to UDP. This is here to have the same interface as the TCPHandler."""
        pass