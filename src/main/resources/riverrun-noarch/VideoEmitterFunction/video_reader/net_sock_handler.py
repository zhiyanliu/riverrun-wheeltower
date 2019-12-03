import socket
import socketserver
import struct


class VideoPacketNetSocketHandler(socketserver.StreamRequestHandler):
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
        super(VideoPacketNetSocketHandler, self).setup()
        self._sock_fd = self.rfile.fileno()
        self._set_keepalive(after_idle_sec=30)
        self.connection.settimeout(30)  # seconds

    def finish(self):
        super(VideoPacketNetSocketHandler, self).finish()
        print("video packet handle session (for socket fd #%d) exits" % self._sock_fd)

    def handle(self):
        try:
            while not self.rfile.closed:
                video_packet_buff_len_buff = self.rfile.read(4)  # big-endian, unsigned int (4 bytes)
                if len(video_packet_buff_len_buff) == 0:
                    return  # EOF
                video_packet_buff_len = struct.unpack("!I", video_packet_buff_len_buff)[0]
                if video_packet_buff_len <= 0:
                    print("invalid length of video packet received: %d, ignored" % video_packet_buff_len)
                    continue
                video_packet_buff = self.rfile.read(video_packet_buff_len)  # char[]
                if len(video_packet_buff) == 0:
                    return  # EOF
                video_packet_buff = struct.unpack('%ds' % video_packet_buff_len, video_packet_buff)[0]

                ret = self._handle_video_packet(video_packet_buff)
                if not ret:
                    break
        except (socket.timeout,  # for python timeout way, connection.settimeout()
                TimeoutError):  # Connection timed out (errno = 110), for OS TCP keepalive way, _set_keepalive()
            print("the client (socket fd #%d) is gone" % self._sock_fd)
        except struct.error as e:
            print("invalid PDU received: %s" % str(e))

    def _handle_video_packet(self, video_packet_buff):
        try:
            self.server.data_pipe_w.send(video_packet_buff)
        except ValueError as e:  # failed to write pipe connection
            print("WARN: failed to send video packet to the pipe: %s" % str(e))

        try:
            # to block wait frame reader ready
            self.server.ack_pipe_r.recv()
        except EOFError:  # write pipe connection closed
            print("BUG: write pipe connection should not be closed before server finish, server exits")
            return False  # no more metadata frame need to handle
        except Exception as e:
            print("WARN: failed to receive ack from the pipe: %s" % str(e))

        return True
