import multiprocessing
import os
import socketserver

from video_reader import net_sock_handler
from video_reader import video_reader


class _VideoPacketNetSocketServer(socketserver.ForkingMixIn, socketserver.TCPServer):
    def __init__(self, data_pipe_w, ack_pipe_r,
                 server_address, request_handler_class, bind_and_activate=True):
        super(_VideoPacketNetSocketServer, self).__init__(server_address, request_handler_class, bind_and_activate)
        self.data_pipe_w = data_pipe_w
        self.ack_pipe_r = ack_pipe_r
        self.connection_count = 0

    def verify_request(self, request, client_address):
        if self.connection_count < 1:  # only one client allowed
            self.connection_count += 1
            print("a video packet TCP client connected, connections = %d" % self.connection_count)
            return True
        else:
            print("WARN: reject a connecting due to video packet TCP client amount limit, connections = %d" %
                  self.connection_count)
            return False

    def close_request(self, request):
        super(_VideoPacketNetSocketServer, self).close_request(request)
        self.connection_count -= 1
        print("a video packet TCP client disconnected, connections = %d" % self.connection_count)


class VideoPacketNetSocketReader(video_reader.VideoPacketReader):
    def __init__(self, port=9526):
        self._data_pipe_r, self._data_pipe_w = multiprocessing.Pipe(False)
        self._ack_pipe_r, self._ack_pipe_w = multiprocessing.Pipe(False)
        self._server = _VideoPacketNetSocketServer(self._data_pipe_w, self._ack_pipe_r,
                                                   ("0.0.0.0", port), net_sock_handler.VideoPacketNetSocketHandler,
                                                   bind_and_activate=False)
        self._run_api_server()
        print("net socket based video packet reader created, pid = %d, port = %d" % (os.getpid(), port))

    def _run_api_server(self):
        try:
            self._server.server_bind()
            self._server.server_activate()
            self._server.serve_forever()
        except:
            self._server.server_close()
            raise

    def read(self):
        try:
            rtp_pkt = self._data_pipe_r.recv()
        except EOFError:  # write pipe connection closed
            print("BUG: write pipe connection should not be closed before reader release")
            return False, None
        except Exception as e:
            print("failed to receive video packet from the pipe: %s" % str(e))
            return False, None

        try:
            self._ack_pipe_w.send("")
        except ValueError as e:
            print("WARN: failed to send ack to the pipe: %s" % str(e))

        return True, rtp_pkt

    def release(self):
        self._server.shutdown()
        self._server.server_close()
        self._data_pipe_r.close()
        self._data_pipe_w.close()
        self._ack_pipe_r.close()
        self._ack_pipe_w.close()
        print("net socket based video packet released, pid = %d" % os.getpid())
