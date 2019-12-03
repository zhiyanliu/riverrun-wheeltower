import multiprocessing

from frame_reader import frame_reader
from frame_reader import net_sock_server
from frame_reader import process


class FrameNetSocketReader(frame_reader.FrameReader):
    def __init__(self, port=9525):
        self._data_pipe_r, self._data_pipe_w = multiprocessing.Pipe(False)
        self._ack_pipe_r, self._ack_pipe_w = multiprocessing.Pipe(False)
        self._semaphore = multiprocessing.BoundedSemaphore(1)  # no concurrency allowed
        self._server_process = process.ServerProcess("metadata frame net socket reading process",
                                                     net_sock_server.frame_net_socket_reader_server,
                                                     self._data_pipe_w, self._ack_pipe_r, self._semaphore, port)
        ret = self._server_process.start()
        if ret:
            print("%s is running" % self._server_process.name())

        print("net socket based frame reader created, port = %d" % port)

    def read(self):
        try:
            meta_frame_timestamp, meta_frame_buff = self._data_pipe_r.recv()
        except EOFError:  # write pipe connection closed
            print("BUG: write pipe connection should not be closed before reader release")
            return False, -1, None
        except Exception as e:
            print("failed to receive metadata frame from the pipe: %s" % str(e))
            return False, -1, None

        try:
            self._ack_pipe_w.send("")
        except ValueError as e:
            print("WARN: failed to send ack to the pipe: %s" % str(e))

        return True, meta_frame_timestamp, meta_frame_buff

    def release(self):
        self._server_process.stop()

        self._data_pipe_r.close()
        self._data_pipe_w.close()
        self._ack_pipe_r.close()
        self._ack_pipe_w.close()

        print("net socket based frame reader released")
