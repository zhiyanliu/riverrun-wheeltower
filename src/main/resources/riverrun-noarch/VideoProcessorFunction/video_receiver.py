import os
import socket

import zmq


class VideoRTPUDPReceiver:
    def __init__(self, port=9529):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(('0.0.0.0', port))
        print("video RTP packet UDP receiver created, pid = %d, port = %d" % (os.getpid(), port))

    def take(self):
        try:
            rtp_pkt, _remote_addr = self.sock.recvfrom(4096)
            if len(rtp_pkt) == 0:  # defence
                print("WARN: read an emtpy RTP packet from UDP network, ignored")
                return False, None
        except Exception as e:
            print("failed to receive RTP packet: %s" % str(e))
            return False, None
        return True, rtp_pkt

    def release(self):
        self.sock.close()
        print("video RTP packet UDP receiver released, pid = %d" % os.getpid())


class VideoRTPTCPReceiver:
    def __init__(self, port=9530):
        self.zmq_context = zmq.Context.instance()
        self.zmq_socket = self.zmq_context.socket(zmq.REP)
        self.zmq_socket.bind("tcp://*:%d" % port)
        print("video RTP packet TCP receiver created, pid = %d, port = %d" % (os.getpid(), port))

    def take(self):
        try:
            rtp_pkt = self.zmq_socket.recv(copy=True)
            self.zmq_socket.send(''.encode())  # receive the reply message
            if len(rtp_pkt) == 0:  # defence
                print("WARN: read an emtpy RTP packet from TCP network, ignored")
                return False, None
        except Exception as e:
            print("failed to receive RTP packet: %s" % str(e))
            return False, None
        return True, rtp_pkt

    def release(self):
        self.zmq_socket.close()
        print("video RTP packet TCP receiver released, pid = %d" % os.getpid())
