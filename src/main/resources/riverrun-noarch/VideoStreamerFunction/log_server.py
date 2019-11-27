import multiprocessing
import multiprocessing.queues

import base_server


class LoggingServer(base_server.Server):
    def __init__(self, name, stat_queue, sync_pkt_queue, rtp_pkt_decoder_class, source_id):
        super(LoggingServer, self).__init__(name, stat_queue)
        if sync_pkt_queue is None:
            raise Exception("synchronized packet queue is None")
        if rtp_pkt_decoder_class is None:
            raise Exception("RTP packet decoder class is None")
        self._sync_pkt_queue = sync_pkt_queue
        self._source_id = source_id
        self._rtp_pkt_decoder = rtp_pkt_decoder_class(self._source_id)
        # logging indicator
        self._received_sync_pkt_count = 0
        self._latest_received_rtp_timestamp = None

    def _log_routine(self):
        if self._latest_received_rtp_timestamp is not None:
            print("the number of received RTP packet from the source #%d in last 5 seconds: %d" %
                  (self._source_id, self._received_sync_pkt_count))
            print("latest received timestamp of synchronized packet: %d" % self._latest_received_rtp_timestamp)
            # reset logging indicator
            self._received_sync_pkt_count = 0
            self._latest_received_rtp_timestamp = None

        self._start_log_routine()

    def serve(self):
        while True:
            try:
                while not self._stop_flag.is_set():
                    _, self._latest_received_rtp_timestamp, rtp_pkt = self._sync_pkt_queue.get(timeout=1)

                    self._received_sync_pkt_count += 1
                    self._rtp_pkt_decoder.put(rtp_pkt)

                break  # server stopped
            except multiprocessing.queues.Empty:
                pass  # timeout just for server stop checking, ignore safely

    def release(self):
        super(LoggingServer, self).release()
        if self._rtp_pkt_decoder is not None:  # to prevent re-entry
            self._rtp_pkt_decoder.release()
            self._rtp_pkt_decoder = None
