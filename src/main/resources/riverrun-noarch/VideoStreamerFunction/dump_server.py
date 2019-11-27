import multiprocessing
import multiprocessing.queues
import os
import struct

import base_server
import constants


class DumpServer(base_server.Server):
    def __init__(self, name, stat_queue, sync_pkt_queue, source_id):
        super(DumpServer, self).__init__(name, stat_queue)
        if sync_pkt_queue is None:
            raise Exception("synchronized packet queue is None")
        self._sync_pkt_queue = sync_pkt_queue
        self._source_id = source_id

        try:
            # RTP packet dump file
            rtp_pkt_file_path = constants.get_rtp_packet_file_save_path()
            rtp_pkt_file_dir = os.path.dirname(rtp_pkt_file_path)
            if not os.path.exists(rtp_pkt_file_dir):
                os.makedirs(rtp_pkt_file_dir)
            self._rtp_pkt_file = open(rtp_pkt_file_path, "wb+")
        except Exception as e:
            print("failed to open RTP packet dump file: %s" % str(e))
            self._rtp_pkt_file = None

        try:
            # metadata frame dump file
            frame_file_path = constants.get_metadata_frame_file_save_path()
            frame_file_dir = os.path.dirname(frame_file_path)
            if not os.path.exists(frame_file_dir):
                os.makedirs(frame_file_dir)
            self._meta_frame_file = open(frame_file_path, "wb+")
        except Exception as e:
            print("failed to open metadata frame dump file: %s" % str(e))
            self._meta_frame_file = None

    def serve(self):
        while True:
            try:
                while not self._stop_flag.is_set():
                    meta_frame_buff, timestamp_rtp, rtp_pkt = self._sync_pkt_queue.get(timeout=1)
                    self._dump_meta_frame_in_net_sock_format(timestamp_rtp, meta_frame_buff)
                    self._dump_rtp_pkt_in_net_sock_format(rtp_pkt)

                break  # server stopped
            except multiprocessing.queues.Empty:
                pass  # ignore safely

    def _dump_meta_frame_in_net_sock_format(self, timestamp, meta_frame_buff):
        meta_frame_buff_len = len(meta_frame_buff)

        buff = struct.pack(
            # unsigned int (4 bytes, big-endian), unsigned int (4 bytes, big-endian), char[]
            "!II%ds" % meta_frame_buff_len, timestamp, meta_frame_buff_len, meta_frame_buff)

        try:
            self._meta_frame_file.write(buff)
        except Exception as e:
            print("failed to write metadata frame dump file: %s" % str(e))

    def _dump_rtp_pkt_in_net_sock_format(self, rtp_pkt):
        rtp_pkt_len = len(rtp_pkt)

        buff = struct.pack(
            # unsigned int (4 bytes, big-endian), char[]
            "!I%ds" % rtp_pkt_len, rtp_pkt_len, rtp_pkt)

        try:
            self._rtp_pkt_file.write(buff)
        except Exception as e:
            print("failed to write RTP packet dump file: %s" % str(e))

    def release(self):
        super(DumpServer, self).release()
        if self._rtp_pkt_file is not None:
            self._rtp_pkt_file.close()
        if self._meta_frame_file is not None:
            self._meta_frame_file.close()
