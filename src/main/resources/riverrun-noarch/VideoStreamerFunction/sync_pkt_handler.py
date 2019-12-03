import multiprocessing
import socket
import socketserver
import struct
import threading

import google.protobuf.message

import constants
import process
import rtp_pkt_decoder
import server
import x2_pb2


def _parse_timestamp(rtp_pkt):
    try:
        timestamp = struct.unpack('!i', rtp_pkt[4:8])[0]
        return True, timestamp
    except Exception as e:
        print("failed to parse RTP packet: %s" % str(e))
        return False, None


class SyncPacketHandler(socketserver.StreamRequestHandler):
    def _start_heartbeat_routine(self):
        self._heartbeat_timer = threading.Timer(self._heartbeat_interval, self._heartbeat_routine)
        self._heartbeat_timer.start()

    def _heartbeat_routine(self):
        try:
            self.wfile.write(socket.gethostname().encode())
            print("sent heartbeat to the client (source id #%d)" % self._source_id)
            self._start_heartbeat_routine()
        except socket.error:
            if not self.wfile.closed:
                self.wfile.close()
            if not self.rfile.closed:
                self.rfile.close()
            print("the client (source id #%d) is gone" % self._source_id)

    def _set_keepalive(self, after_idle_sec=60, interval_sec=60, max_fails=10):
        """Set TCP keepalive on an open socket.
            It activates after after_idle_sec of idleness,
            then sends a keepalive ping once every interval_sec,
            and closes the connection after max_fails failed ping
            """
        self.connection.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        self.connection.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPIDLE, after_idle_sec)
        self.connection.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPINTVL, interval_sec)
        self.connection.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPCNT, max_fails)

    def _start_log_routine(self):
        self._log_timer = threading.Timer(5, self._log_routine)
        self._log_timer.start()

    def _log_routine(self):
        # log sent synchronized packet count
        print("count of received synchronized packet from the source #%d in last 5 seconds: %d" %
              (self._source_id, self._received_count))
        self._received_count = 0
        self._start_log_routine()

    def setup(self):
        super(SyncPacketHandler, self).setup()
        self._source_id = self.rfile.fileno()

        # log received synchronized packet count
        self._received_count = 0
        self._start_log_routine()

        self._heartbeat_interval = constants.get_sync_pkt_server_heartbeat_interval_sec()
        # currently we use own heartbeat mechanism to help client to detect if server is alive
        # self._set_keepalive(self._heartbeat_interval, self._heartbeat_interval, 1)
        # send own heartbeat from server to client for client side detection
        self._start_heartbeat_routine()
        # due to we haven't heartbeat from client to server to help server to detect if client is alive
        # we use python socket timeout mechanism for server side detection
        self.connection.settimeout(self._heartbeat_interval)

        self._log_queue = multiprocessing.Queue(maxsize=self.server.sync_pkt_queue_size)

        self._sync_pkt_log_server_process = process.ServerProcess(
            "synchronized packet logging process (for client source id #%d)" % self._source_id,
            server.sync_pkt_logging_server_creator,
            self.server.stat_queue,
            self._log_queue,
            rtp_pkt_decoder.RTPPacketSimpleDecoder,
            self._source_id)

        ret = self._sync_pkt_log_server_process.start()
        if ret:
            print("%s is running" % self._sync_pkt_log_server_process.name())

        self._dump_queue = multiprocessing.Queue(maxsize=self.server.sync_pkt_queue_size)

        self._sync_pkt_dump_server_process = process.ServerProcess(
            "synchronized packet dump process (for client source id #%d)" % self._source_id,
            server.sync_pkt_dump_server_creator,
            self.server.stat_queue,
            self._dump_queue,
            self._source_id)

        ret = self._sync_pkt_dump_server_process.start()
        if ret:
            print("%s is running" % self._sync_pkt_dump_server_process.name())

    def finish(self):
        super(SyncPacketHandler, self).finish()
        # will flush queue
        self._log_queue.close()
        self._dump_queue.close()
        # stop server process
        self._sync_pkt_log_server_process.stop()
        self._sync_pkt_dump_server_process.stop()
        # stop heartbeat
        if self._heartbeat_timer is not None:
            self._heartbeat_timer.cancel()
        print("synchronized packet handle server (for client source id #%d) exits" % self._source_id)

    def handle(self):
        try:
            while not self.rfile.closed:
                meta_frame_buff_len_buff = self.rfile.read(4)  # big-endian, unsigned int (4 bytes)
                if len(meta_frame_buff_len_buff) == 0:
                    return  # EOF
                meta_frame_buff_len = struct.unpack("!I", meta_frame_buff_len_buff)[0]
                if meta_frame_buff_len > 0:
                    meta_frame_buff = self.rfile.read(meta_frame_buff_len)  # char[]
                    if len(meta_frame_buff) == 0:
                        return  # EOF
                    meta_frame_buff = struct.unpack('%ds' % meta_frame_buff_len, meta_frame_buff)[0]
                else:  # should meta_frame_buff_len == 0
                    meta_frame_buff = None

                rtp_pkt_buff_len_buff = self.rfile.read(4)  # big-endian, unsigned int (4 bytes)
                if len(rtp_pkt_buff_len_buff) == 0:
                    return  # EOF
                rtp_pkt_buff_len = struct.unpack("!I", rtp_pkt_buff_len_buff)[0]
                rtp_pkt_buff = self.rfile.read(rtp_pkt_buff_len)  # char[]
                if len(rtp_pkt_buff) == 0:
                    return  # EOF
                rtp_pkt_buff = struct.unpack('%ds' % rtp_pkt_buff_len, rtp_pkt_buff)[0]

                self._handle_sync_pkt(rtp_pkt_buff, meta_frame_buff)
        except (socket.timeout,  # for python timeout way, connection.settimeout()
                TimeoutError):  # Connection timed out (errno = 110), for OS TCP keepalive way, _set_keepalive()
            print("the client (source id #%d) is gone" % self._source_id)
        except struct.error as e:
            print("invalid PDU received: %s" % str(e))

    def _handle_sync_pkt(self, rtp_pkt_buff, meta_frame_buff):
        try:
            if len(rtp_pkt_buff) == 0:
                raise Exception("RTP packet is empty")

            ret, timestamp_rtp = _parse_timestamp(rtp_pkt_buff)
            if not ret:
                raise Exception("failed to parse RTP packet")

            if meta_frame_buff is not None:  # do not verify empty "drop" metadata frame
                try:
                    meta_frame = x2_pb2.FrameMessage()
                    meta_frame.ParseFromString(meta_frame_buff)
                    if meta_frame.smart_msg_ is None or meta_frame.smart_msg_.timestamp_ is None:
                        raise Exception("smart message or timestamp in metadata frame is empty")

                    timestamp_fm = meta_frame.smart_msg_.timestamp_

                    if (timestamp_fm > 0 and  # RTP packet synchronized with a valid metadata frame
                            timestamp_fm != timestamp_rtp):
                        print("BUG: invalid synchronized packet received: the RTP packet timestamp"
                              "is not equal to the metadata frame timestamp (%d != %d), "
                              "it seems like a BUG in client implementation, the packet ignored" %
                              (timestamp_fm, timestamp_rtp))
                except google.protobuf.message.DecodeError:
                    # ignore parsing message error
                    # it may caused by client is using own metadata frame format instead of Horizon's
                    pass

        except Exception as e:
            print("invalid synchronized packet received: %s" % str(e))
            return

        self._received_count += 1

        while True:
            try:
                self._log_queue.put((meta_frame_buff, timestamp_rtp, rtp_pkt_buff), timeout=1)
                break
            except multiprocessing.queues.Full:
                print("WARN: logging server is slow, "
                      "input RTP packet and metadata frame are rejected due to busy, retry")
        while True:
            try:
                self._dump_queue.put((meta_frame_buff, timestamp_rtp, rtp_pkt_buff), timeout=1)
                break
            except multiprocessing.queues.Full:
                print("WARN: dump server is slow, "
                      "input RTP packet and metadata frame are rejected due to busy, retry")
