import os
import socket

import zmq


class VideoRTPPacketSubscriber:
    def __init__(self, port=9531, topic="rtp"):
        self.zmq_context = zmq.Context.instance()
        self.zmq_socket = self.zmq_context.socket(zmq.SUB)
        identity = "riverrun-video-processor-video-packet-subscriber@%s" % socket.gethostname()
        self.zmq_socket.setsockopt(zmq.IDENTITY, identity.encode())
        self.zmq_socket.setsockopt(zmq.SUBSCRIBE, topic.encode())
        # drop message to prevent memory overflow
        self.zmq_socket.setsockopt(zmq.RCVHWM, 100)
        # set option before bind
        self.zmq_socket.bind("tcp://*:%d" % port)
        print("video RTP packet subscriber created, pid = %d, port = %d, topic = %s" % (os.getpid(), port, topic))

    def take(self):
        try:
            data = self.zmq_socket.recv(copy=True)
            _topic, rtp_pkt = data.split(" ".encode(), 1)
        except Exception as e:
            print("invalid RTP packet received: %s" % str(e))
            return False, None
        return True, rtp_pkt

    def release(self):
        self.zmq_socket.close()
        print("frame subscriber released, pid = %d" % os.getpid())
