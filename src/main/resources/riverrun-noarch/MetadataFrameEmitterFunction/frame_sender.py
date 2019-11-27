import os
import struct

import zmq

import constants


class FrameSender:
    def __init__(self, ip, port=9527):
        self.ip = ip
        self.port = port
        self.zmq_context = zmq.Context.instance()
        self._connect_socket()
        print("frame sender created, pid = %d, target = %s:%d" % (os.getpid(), self.ip, self.port))

    def _connect_socket(self):
        self.zmq_socket = self.zmq_context.socket(zmq.REQ)
        self.zmq_socket.setsockopt(zmq.RCVTIMEO, constants.get_request_rely_timeout())  # milliseconds
        # set option before connect
        self.zmq_socket.connect("tcp://%s:%d" % (self.ip, self.port))

    def _reset_my_socket(self):
        self.zmq_socket.close()
        self._connect_socket()

    def emit(self, meta_frame_timestamp, meta_frame_buff):
        buff = struct.pack(
            # unsigned int (4 bytes, big-endian), char[]
            "!I%ds" % len(meta_frame_buff), meta_frame_timestamp, meta_frame_buff)

        self.zmq_socket.send(buff, copy=False)
        try:
            reply = self.zmq_socket.recv()  # receive the reply message
            return reply
        except zmq.Again:  # timeout
            print("timeout, did not receive frame message sending reply")
            self._reset_my_socket()
            return None

    def release(self):
        self.zmq_socket.close()
        print("frame sender released, pid = %d, target = %s:%d" % (os.getpid(), self.ip, self.port))
