import os
import socket
import struct

import zmq


class FrameSubscriber:
    def __init__(self, port=9528, topic="md"):
        self.zmq_context = zmq.Context.instance()
        self.zmq_socket = self.zmq_context.socket(zmq.SUB)
        identity = "riverrun-video-processor-metadata-frame-subscriber@%s" % socket.gethostname()
        self.zmq_socket.setsockopt(zmq.IDENTITY, identity.encode())
        self.zmq_socket.setsockopt(zmq.SUBSCRIBE, topic.encode())
        # drop message to prevent memory overflow
        self.zmq_socket.setsockopt(zmq.RCVHWM, 100)
        # set option before bind
        self.zmq_socket.bind("tcp://*:%d" % port)
        print("frame subscriber created, pid = %d, port = %d, topic = %s" % (os.getpid(), port, topic))

    def take(self):
        try:
            data = self.zmq_socket.recv(copy=True)
            _topic, buff = data.split(" ".encode(), 1)
            meta_frame_timestamp = struct.unpack("!I", buff[:struct.calcsize("!I")])[0]
            meta_frame_buff = buff[struct.calcsize("!I"):]
        except Exception as e:
            print("failed to receive metadata frame timestamp and buffer: %s" % str(e))
            return False, -1, None
        return True, meta_frame_timestamp, meta_frame_buff

    def release(self):
        self.zmq_socket.close()
        print("frame subscriber released, pid = %d" % os.getpid())
