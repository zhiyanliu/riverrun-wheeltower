import datetime
import os
import struct
import socket
import threading
import time

import constants


class SyncPacketTCPSender:
    def __init__(self, ip, port=9532):
        self.ip = ip
        self.port = port
        self._connected = False
        print("synchronized packet TCP sender created, pid = %d, target = %s:%d" % (os.getpid(), self.ip, self.port))

    def _start_heartbeat_read_routine(self):
        self._latest_heartbeat_timestamp = datetime.datetime.now()
        self._heartbeat_read_thread = threading.Thread(target=self._heartbeat_read_routine)
        self._heartbeat_read_thread.start()

    def _heartbeat_read_routine(self):
        while self._connected:
            try:
                peer_hostname_buff = self.sock.recv(1024)
                if len(peer_hostname_buff) == 0:
                    print("synchronized packet TCP server %s:%d is gone" % (self.ip, self.port))
                    return  # EOF
                self._latest_heartbeat_timestamp = datetime.datetime.now()
                print("heartbeat received from the synchronized packet TCP server, target = %s:%d, hostname = %s" %
                      (self.ip, self.port, peer_hostname_buff.decode()))
            except Exception as e:
                print("failed to read heartbeat from the TCP server, target = %s:%d: %s" %
                      (self.ip, self.port, str(e)))

    def _start_heartbeat_check_routine(self):
        self._heartbeat_timeout = constants.get_sync_pkt_server_heartbeat_timeout_sec()
        self._heartbeat_check_thread = threading.Thread(target=self._heartbeat_check_routine)
        self._heartbeat_check_thread.start()

    def _heartbeat_check_routine(self):
        while self._connected:
            delta = datetime.datetime.now() - self._latest_heartbeat_timestamp
            if delta.seconds > self._heartbeat_timeout:
                print("WARN: synchronized packet TCP server heartbeat timeout, target = %s:%d" % (self.ip, self.port))
            time.sleep(1)

    def _connect(self):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((self.ip, self.port))
            self._connected = True
            # start to handle heartbeat
            self._heartbeat_read_thread = None
            self.__heartbeat_check_thread = None
            self._start_heartbeat_read_routine()
            self._start_heartbeat_check_routine()
            print("synchronized packet TCP sender connected, target = %s:%d" % (self.ip, self.port))
        except Exception as e:
            print("failed to connect the TCP server, target = %s:%d: %s" % (self.ip, self.port, str(e)))
            self._reset_conn()

    def _reset_conn(self):
        if self._connected:
            self._connected = False
            self.sock.close()
            # wait heartbeat handling to stop
            if self.__heartbeat_check_thread is not None:
                self._heartbeat_check_thread.join()
            if self._heartbeat_read_thread is not None:
                self._heartbeat_read_thread.join()
            print("synchronized packet TCP sender disconnected, target = %s:%d" % (self.ip, self.port))

    def emit(self, rtp_pkt_buff, meta_frame_buff):
        if not self._connected:
            self._connect()

        if not self._connected:
            print("WARN: can not connect to the TCP server, skip sending the synchronized packet")
            return

        rtp_pkt_buff_len = len(rtp_pkt_buff)
        meta_frame_buff_len = len(meta_frame_buff)

        if meta_frame_buff_len > 0:
            buff = struct.pack(
                # unsigned int (4 bytes, big-endian), char[], unsigned int (4 bytes, big-endian), char[]
                "!I%dsI%ds" % (meta_frame_buff_len, rtp_pkt_buff_len),
                meta_frame_buff_len, meta_frame_buff, rtp_pkt_buff_len, rtp_pkt_buff)
        else:  # should meta_frame_buff_len == 0:
            buff = struct.pack(
                # unsigned int (4 bytes, big-endian), unsigned int (4 bytes, big-endian), char[]
                "!II%ds" % rtp_pkt_buff_len, 0, rtp_pkt_buff_len, rtp_pkt_buff)

        try:
            self.sock.sendall(buff)
        except Exception as e:
            print("failed to send the synchronized packet, target = %s:%d: %s" % (self.ip, self.port, str(e)))
            self._reset_conn()

    def release(self):
        self._reset_conn()
        print("synced packet TCP sender released, pid = %d" % os.getpid())


class SyncPacketNoneSender:
    def __init__(self):
        print("synchronized packet NONE sender created, pid = %d" % os.getpid())

    def emit(self, rtp_pkt_buff, meta_frame_buff):
        rtp_pkt_buff_len = len(rtp_pkt_buff)
        meta_frame_buff_len = len(meta_frame_buff)
        print("emitted a packet, RTP packet buffer length = %d, metadata frame buffer length = %d" %
              (rtp_pkt_buff_len, meta_frame_buff_len))

    def release(self):
        print("synchronized packet packet NONE sender released, pid = %d" % os.getpid())


_empty_meta_frame_buff = b""


class SyncPacketCombiner:
    def combine(self, rtp_pkt, meta_frame):
        if meta_frame is None:
            return True, (rtp_pkt.buff, _empty_meta_frame_buff)
        else:
            return True, (rtp_pkt.buff, meta_frame.buff)
