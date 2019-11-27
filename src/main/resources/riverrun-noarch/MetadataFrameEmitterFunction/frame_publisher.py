import os
import struct

import zmq


class FramePublisher:
    def __init__(self, ip, port=9528, topic="md"):
        self.ip = ip
        self.port = port
        self.zmq_context = zmq.Context.instance()
        self.zmq_socket = self.zmq_context.socket(zmq.PUB)
        # drop message to prevent memory overflow
        self.zmq_socket.setsockopt(zmq.SNDHWM, 100)
        # set option before connect
        self.zmq_socket.connect("tcp://%s:%d" % (ip, port))
        self.topic = topic
        print("frame publisher created, pid = %d, target = %s:%d, topic = %s" %
              (os.getpid(), self.ip, self.port, self.topic))

    def emit(self, meta_frame_timestamp, meta_frame_buff):
        buff = struct.pack(
            # unsigned int (4 bytes, big-endian), char[]
            "!I%ds" % len(meta_frame_buff), meta_frame_timestamp, meta_frame_buff)

        self.zmq_socket.send(self.topic.encode() + " ".encode() + buff, copy=False)

    def release(self):
        self.zmq_socket.close()
        print("frame publisher released, pid = %d, target = %s:%d" % (os.getpid(), self.ip, self.port))
