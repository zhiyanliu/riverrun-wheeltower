import base_server
import frame


class FrameHandleServer(base_server.Server):
    def __init__(self, name, frame_throttle_pipe_r, frame_handle_pipe_w):
        super(FrameHandleServer, self).__init__(name)
        if frame_throttle_pipe_r is None:
            raise Exception("throttle read pipe connection is None")
        if frame_handle_pipe_w is None:
            raise Exception("handle write pipe connection is None")
        self._frame_throttle_pipe_r = frame_throttle_pipe_r
        self._frame_handle_pipe_w = frame_handle_pipe_w
        self._latest_received_timestamp = 0

    def _log_routine(self):
        print("latest received metadata frame timestamp: %d" % self._latest_received_timestamp)
        self._start_log_routine()

    def serve(self):
        while not self._stop_flag.is_set():
            try:
                # poll with timeout first just for server stop checking
                ret = self._frame_throttle_pipe_r.poll(1)
                if not ret:  # no more data
                    continue
                meta_frame_timestamp, meta_frame_buff = self._frame_throttle_pipe_r.recv()
            except EOFError:  # write pipe connection closed
                print("BUG: write pipe connection should not be closed before server finish, server exits")
                return  # no more packet need to handle
            except Exception as e:
                print("WARN: failed to receive metadata frame from the pipe: %s" % str(e))
                continue

            meta_frame = frame.MetaFrame(meta_frame_timestamp, meta_frame_buff)
            self._latest_received_timestamp = meta_frame.timestamp

            try:
                self._frame_handle_pipe_w.send(meta_frame)
            except ValueError as e:
                print("WARN: failed to send metadata frame to the pipe: %s" % str(e))
                continue
