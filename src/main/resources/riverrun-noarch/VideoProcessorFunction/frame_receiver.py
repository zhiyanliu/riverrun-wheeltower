import os
import struct

import zmq


class FrameReceiver:
    def __init__(self, port=9527):
        self.zmq_context = zmq.Context.instance()
        self.zmq_socket = self.zmq_context.socket(zmq.REP)
        self.zmq_socket.bind("tcp://*:%d" % port)
        print("frame receiver created, pid = %d, port = %d" % (os.getpid(), port))

    def take(self):
        try:
            buff = self.zmq_socket.recv(copy=True)
            self.zmq_socket.send(''.encode())  # receive the reply message
            if len(buff) == 0:
                raise Exception("empty metadata frame buffer received")
            meta_frame_timestamp = struct.unpack("!I", buff[:struct.calcsize("!I")])[0]
            meta_frame_buff = buff[struct.calcsize("!I"):]
        except Exception as e:
            print("failed to receive metadata frame timestamp and buffer: %s" % str(e))
            return False, -1, None
        return True, meta_frame_timestamp, meta_frame_buff

    def release(self):
        self.zmq_socket.close()
        print("frame receiver released, pid = %d" % os.getpid())
