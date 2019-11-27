import base_server
import sync_pkt_comm


class SyncPacketEmitServer(base_server.Server):
    def __init__(self, name, sync_pkt_emit_pipe_r):
        super(SyncPacketEmitServer, self).__init__(name)
        if sync_pkt_emit_pipe_r is None:
            raise Exception("synchronized packet emit pipe reader is None")
        self._sync_pkt_emit_pipe_r = sync_pkt_emit_pipe_r
        # log sent synchronized packet count
        self._sent_count = 0
        self._emitter = sync_pkt_comm.create_emitter()

    def _log_routine(self):
        # log sent synchronized packet count
        print("count of sent synchronized packet in last 5 seconds: %d" % self._sent_count)
        self._sent_count = 0
        self._start_log_routine()

    def serve(self):
        while not self._stop_flag.is_set():
            try:
                # poll with timeout first just for server stop checking
                ret = self._sync_pkt_emit_pipe_r.poll(1)
                if not ret:  # no more data
                    continue
                rtp_pkt_buff, meta_frame_buff = self._sync_pkt_emit_pipe_r.recv()
            except EOFError:  # write pipe connection closed
                print("BUG: write pipe connection should not be closed before server finish, server exits")
                return  # no more packet need to emit
            except Exception as e:
                print("WARN: failed to receive synchronized packet from the pipe: %s" % str(e))
                continue

            self._emitter.emit(rtp_pkt_buff, meta_frame_buff)
            self._sent_count += 1

    def release(self):
        super(SyncPacketEmitServer, self).release()
        self._emitter.release()
