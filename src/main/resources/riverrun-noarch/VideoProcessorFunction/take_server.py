import base_server
import frame_comm
import rtp_parse
import video_comm


class TakeServer(base_server.Server):
    def __init__(self, name, take_pipe_w):
        super(TakeServer, self).__init__(name)
        if take_pipe_w is None:
            raise Exception("take write pipe connection is None")
        self._take_pipe_w = take_pipe_w


class FrameTakeServer(TakeServer):
    def __init__(self, name, take_pipe_w):
        super(FrameTakeServer, self).__init__(name, take_pipe_w)
        self._taker = frame_comm.create_taker()
        if self._taker is None:
            raise Exception("failed to create metadata frame taking server")

    def serve(self):
        while True:
            try:
                while not self._stop_flag.is_set():
                    ret, meta_frame_timestamp, meta_frame_buff = self._taker.take()
                    if not ret:
                        print("failed to take metadata frame, ignored")
                        continue

                    try:
                        self._take_pipe_w.send((meta_frame_timestamp, meta_frame_buff))
                    except ValueError as e:
                        print("WARN: failed to send metadata frame to the pipe: %s" % str(e))
                        continue

                break  # server stopped
            except Exception as e:
                print("failed to take metadata frame: %s" % str(e))

    def release(self):
        super(FrameTakeServer, self).release()
        self._taker.release()


class VideoTakeServer(TakeServer):
    def __init__(self, name, take_queue):
        super(VideoTakeServer, self).__init__(name, take_queue)
        self._taker = video_comm.create_taker()
        if self._taker is None:
            raise Exception("failed to create video packet taking server")
        self._latest_received_timestamp = 0

    def _log_routine(self):
        print("latest received video packet timestamp: %d" % self._latest_received_timestamp)
        self._start_log_routine()

    def serve(self):
        while True:
            try:
                while not self._stop_flag.is_set():
                    ret, video_pkt = self._taker.take()
                    if not ret:
                        print("failed to receive video packet, skip the video packet")
                        continue
                    try:
                        pkt = rtp_parse.RTPPacket(video_pkt)
                    except Exception as e:
                        print("%s, skip the video packet" % str(e))
                        continue

                    self._latest_received_timestamp = pkt.timestamp

                    try:
                        self._take_pipe_w.send(pkt)
                    except ValueError as e:
                        print("WARN: failed to send video packet to the pipe: %s" % str(e))
                        continue

                break  # server stopped
            except Exception as e:
                print("failed to take video packet: %s" % str(e))

    def release(self):
        super(VideoTakeServer, self).release()
        self._taker.release()
