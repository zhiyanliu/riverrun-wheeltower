import os
import socket

import zmq

import constants


class RTPPacketUDPSender:
    def __init__(self, ip, port=9529):
        self.ip = ip
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        print("video RTP packet UDP sender created, pid = %d, target = %s:%d" % (os.getpid(), self.ip, self.port))

    def emit(self, rtp_pkt):  # rtp_pkt should be a bytes-like object
        self.sock.sendto(rtp_pkt, (self.ip, self.port))

    def release(self):
        self.sock.close()
        print("video RTP packet UDP sender released, pid = %d" % os.getpid())


class RTPPacketTCPSender:
    def __init__(self, ip, port=9530):
        self.ip = ip
        self.port = port
        self.zmq_context = zmq.Context.instance()
        self._connect_socket()
        print("video RTP packet TCP sender created, pid = %d, target = %s:%d" % (os.getpid(), self.ip, self.port))

    def _connect_socket(self):
        self.zmq_socket = self.zmq_context.socket(zmq.REQ)
        self.zmq_socket.setsockopt(zmq.RCVTIMEO, constants.get_request_rely_timeout())  # milliseconds
        # set option before connect
        self.zmq_socket.connect("tcp://%s:%d" % (self.ip, self.port))

    def _reset_my_socket(self):
        self.zmq_socket.close()
        self._connect_socket()

    def emit(self, rtp_pkt):
        self.zmq_socket.send(rtp_pkt, copy=False)
        try:
            reply = self.zmq_socket.recv()  # receive the reply message
            return reply
        except zmq.Again:  # timeout
            print("timeout, did not receive RTP packet sending reply")
            self._reset_my_socket()
            return None

    def release(self):
        self.zmq_socket.close()
        print("video RTP packet TCP sender released, pid = %d, target = %s:%d" % (os.getpid(), self.ip, self.port))
