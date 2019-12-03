import socket
import socketserver
import struct
import threading


class FrameNetSocketHandler(socketserver.StreamRequestHandler):
    def _start_log_routine(self):
        self._log_timer = threading.Timer(5, self._log_routine)
        self._log_timer.start()

    def _log_routine(self):
        # log latest read metadata frame timestamp
        if self._latest_timestamp is not None:
            print("latest read metadata frame timestamp: %d" % self._latest_timestamp)
        self._start_log_routine()

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

    def setup(self):
        super(FrameNetSocketHandler, self).setup()
        self._sock_fd = self.rfile.fileno()
        self._set_keepalive(after_idle_sec=30)
        self.connection.settimeout(30)  # seconds

        # latest read metadata frame timestamp
        self._latest_timestamp = None
        self._start_log_routine()

    def finish(self):
        super(FrameNetSocketHandler, self).finish()
        print("frame handle session (for socket fd #%d) exits" % self._sock_fd)

    def handle(self):
        try:
            while not self.rfile.closed:
                meta_frame_timestamp_buff = self.rfile.read(4)  # big-endian, unsigned int (4 bytes)
                if len(meta_frame_timestamp_buff) == 0:
                    return  # EOF
                meta_frame_timestamp = struct.unpack("!I", meta_frame_timestamp_buff)[0]
                if meta_frame_timestamp < 0 or meta_frame_timestamp > 65535:
                    print("invalid timestamp of metadata frame received: %d, ignored" % meta_frame_timestamp)
                    continue

                meta_frame_buff_len_buff = self.rfile.read(4)  # big-endian, unsigned int (4 bytes)
                if len(meta_frame_buff_len_buff) == 0:
                    return  # EOF
                meta_frame_buff_len = struct.unpack("!I", meta_frame_buff_len_buff)[0]
                if meta_frame_buff_len <= 0:
                    print("invalid length of metadata frame received: %d, ignored" % meta_frame_buff_len)
                    continue

                meta_frame_buff = self.rfile.read(meta_frame_buff_len)  # char[]
                if len(meta_frame_buff) == 0:
                    return  # EOF
                meta_frame_buff = struct.unpack('%ds' % meta_frame_buff_len, meta_frame_buff)[0]

                ret = self._handle_meta_frame(meta_frame_timestamp, meta_frame_buff)
                if not ret:
                    break
        except (socket.timeout,  # for python timeout way, connection.settimeout()
                TimeoutError):  # Connection timed out (errno = 110), for OS TCP keepalive way, _set_keepalive()
            print("the client (socket fd #%d) is gone" % self._sock_fd)
        except struct.error as e:
            print("invalid PDU received: %s" % str(e))

    def _handle_meta_frame(self, meta_frame_timestamp, meta_frame_buff):
        try:
            self._latest_timestamp = meta_frame_timestamp

            self.server.data_pipe_w.send((meta_frame_timestamp, meta_frame_buff))
        except ValueError as e:  # failed to write pipe connection
            print("WARN: failed to send metadata frame to the pipe: %s" % str(e))

        try:
            # to block wait frame reader ready
            self.server.ack_pipe_r.recv()
        except EOFError:  # write pipe connection closed
            print("BUG: write pipe connection should not be closed before server finish, server exits")
            return False  # no more metadata frame need to handle
        except Exception as e:
            print("WARN: failed to receive ack from the pipe: %s" % str(e))

        return True
