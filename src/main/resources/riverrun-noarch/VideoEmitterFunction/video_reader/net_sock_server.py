import socketserver

from video_reader import base_server
from video_reader import net_sock_handler


def video_net_socket_reader_server(data_pipe_w, ack_pipe_r, semaphore, port=9526):
    return VideoPacketNetSocketReaderServer(
        "video packet net socket reading server", data_pipe_w, ack_pipe_r, semaphore, port)


class _VideoPacketNetSocketServer(socketserver.ForkingMixIn, socketserver.TCPServer):
    def __init__(self, data_pipe_w, ack_pipe_r, semaphore,
                 server_address, request_handler_class, bind_and_activate=True):
        super(_VideoPacketNetSocketServer, self).__init__(server_address, request_handler_class, bind_and_activate)
        self.data_pipe_w = data_pipe_w
        self.ack_pipe_r = ack_pipe_r
        self._semaphore = semaphore
        self._semaphore_acquired = False

    def verify_request(self, request, client_address):
        self._semaphore_acquired = self._semaphore.acquire(block=False)
        if self._semaphore_acquired:
            print("a video packet TCP client connected, client = %s:%d" % client_address)
            return True
        else:
            print("WARN: reject a connecting due to video packet TCP client max connections limit, "
                  "client = %s:%d" % client_address)
            return False

    def shutdown_request(self, request):
        super(_VideoPacketNetSocketServer, self).close_request(request)
        if self._semaphore_acquired:
            self._semaphore.release()
            print("a video packet TCP client disconnected")
        else:
            print("a video packet TCP client rejected")


class VideoPacketNetSocketReaderServer(base_server.Server):
    def __init__(self, name, data_pipe_w, ack_pipe_r, semaphore, port=9526):
        super(VideoPacketNetSocketReaderServer, self).__init__(name)
        if data_pipe_w is None:
            raise Exception("data write pipe connection is None")
        if ack_pipe_r is None:
            raise Exception("ack read pipe connection is None")

        self._server = _VideoPacketNetSocketServer(data_pipe_w, ack_pipe_r, semaphore,
                                                   ("0.0.0.0", port), net_sock_handler.VideoPacketNetSocketHandler,
                                                   bind_and_activate=False)

    def serve(self):
        try:
            self._server.server_bind()
            self._server.server_activate()
            self._server.serve_forever()
        except Exception as e:
            print("failed to read video packet: %s" % str(e))

    def stop(self):
        super(VideoPacketNetSocketReaderServer, self).stop()
        self._server.shutdown()

    def release(self):
        super(VideoPacketNetSocketReaderServer, self).release()
        self._server.server_close()
