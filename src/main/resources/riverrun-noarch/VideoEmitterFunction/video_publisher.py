import os

import zmq


class RTPPacketPublisher:
    def __init__(self, ip, port=9531, topic="rtp"):
        self.ip = ip
        self.port = port
        self.zmq_context = zmq.Context.instance()
        self.zmq_socket = self.zmq_context.socket(zmq.PUB)
        # drop message to prevent memory overflow
        self.zmq_socket.setsockopt(zmq.SNDHWM, 100)
        # set option before connect
        self.zmq_socket.connect("tcp://%s:%d" % (ip, port))
        self.topic = topic
        print("video RTP packet publisher created, pid = %d, target = %s:%d, topic = %s" %
              (os.getpid(), self.ip, self.port, self.topic))

    def emit(self, rtp_pkt):
        self.zmq_socket.send(self.topic.encode() + " ".encode() + rtp_pkt, copy=False)

    def release(self):
        self.zmq_socket.close()
        print("video  RTP packet publisher released, pid = %d, target = %s:%d" % (os.getpid(), self.ip, self.port))
