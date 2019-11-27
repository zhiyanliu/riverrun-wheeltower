import collections
import threading

import base_server
import constants


class _Sender(threading.Thread):
    def __init__(self, stop_flag, frame_handle_pipe_w, throttle_tolerate_count, queue):
        threading.Thread.__init__(self)
        self._stop_flag = stop_flag
        self._frame_handle_pipe_w = frame_handle_pipe_w
        self._max_count = throttle_tolerate_count
        self._queue = queue
        self._ready = threading.Event()

    def run(self):
        while not self._stop_flag.is_set():
            try:
                meta_frame_timestamp, meta_frame_buff = self._queue.popleft()
                self._frame_handle_pipe_w.send((meta_frame_timestamp, meta_frame_buff))
            except IndexError:  # no elements are present in self._queue
                self._ready.clear()
                self._ready.wait(timeout=1)
            except ValueError as e:  # failed to write pipe connection self._frame_handle_pipe_w
                print("WARN: failed to send metadata frame to the pipe: %s" % str(e))

    def send(self, meta_frame_timestamp, meta_frame_buff):
        queue_len = len(self._queue)
        if queue_len > self._max_count:
            print("WARN: metadata frame throttling, a frame dropped (queue length = %d), " % queue_len)
            return
        self._queue.append((meta_frame_timestamp, meta_frame_buff))
        self._ready.set()


class FrameThrottleServer(base_server.Server):
    def __init__(self, name, frame_take_pipe_r, frame_throttle_pipe_w):
        super(FrameThrottleServer, self).__init__(name)
        if frame_take_pipe_r is None:
            raise Exception("take read pipe connection is None")
        if frame_throttle_pipe_w is None:
            raise Exception("throttle write pipe connection is None")
        self._frame_take_pipe_r = frame_take_pipe_r
        throttle_tolerate_count = constants.get_meta_frame_throttle_tolerate_count()
        self._queue = collections.deque()
        self._sender = _Sender(self._stop_flag, frame_throttle_pipe_w, throttle_tolerate_count, self._queue)

    def _log_routine(self):
        queue_len = len(self._queue)
        if queue_len > 0:
            print("metadata frame is queuing (handle queue length = %d)" % queue_len)
        self._start_log_routine()

    def serve(self):
        self._sender.start()

        while not self._stop_flag.is_set():
            try:
                # poll with timeout first just for server stop checking
                ret = self._frame_take_pipe_r.poll(1)
                if not ret:  # no more data
                    continue
                meta_frame_timestamp, meta_frame_buff = self._frame_take_pipe_r.recv()
            except EOFError:  # write pipe connection closed
                print("BUG: write pipe connection should not be closed before server finish, server exits")
                return  # no more packet need to handle
            except Exception as e:
                print("WARN: failed to receive metadata frame from the pipe: %s" % str(e))
                continue

            self._sender.send(meta_frame_timestamp, meta_frame_buff)

    def release(self):
        super(FrameThrottleServer, self).release()
        self._sender.join()
