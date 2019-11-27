import os
import socketserver

import sync_pkt_handler


class _SyncPacketTCPServer(socketserver.ForkingMixIn, socketserver.TCPServer):
    def __init__(self, stat_queue, sync_pkt_queue_size,
                 server_address, request_handler_class, bind_and_activate=True):
        super(_SyncPacketTCPServer, self).__init__(server_address, request_handler_class, bind_and_activate)
        self.stat_queue = stat_queue
        self.sync_pkt_queue_size = sync_pkt_queue_size


class SyncPacketTCPReceiver:
    def __init__(self, stat_queue, sync_pkt_queue_size=20, port=9532):
        self._server = _SyncPacketTCPServer(stat_queue, sync_pkt_queue_size,
                                            ("0.0.0.0", port), sync_pkt_handler.SyncPacketHandler,
                                            bind_and_activate=False)
        print("synchronized packet TCP receiver created, pid = %d, port = %d" % (os.getpid(), port))

    def run(self):
        try:
            self._server.server_bind()
            self._server.server_activate()
            self._server.serve_forever()
        except:
            self._server.server_close()
            raise

    def shutdown(self):
        self._server.shutdown()

    def release(self):
        self._server.server_close()
        print("synced packet TCP receiver released, pid = %d" % os.getpid())
