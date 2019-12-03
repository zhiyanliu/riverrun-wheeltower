import multiprocessing

from video_reader import net_sock_server
from video_reader import process
from video_reader import video_reader


class VideoPacketNetSocketReader(video_reader.VideoPacketReader):
    def __init__(self, port=9526):
        self._data_pipe_r, self._data_pipe_w = multiprocessing.Pipe(False)
        self._ack_pipe_r, self._ack_pipe_w = multiprocessing.Pipe(False)
        self._semaphore = multiprocessing.BoundedSemaphore(1)  # no concurrency allowed
        self._server_process = process.ServerProcess("video packet net socket reading process",
                                                     net_sock_server.video_net_socket_reader_server,
                                                     self._data_pipe_w, self._ack_pipe_r, self._semaphore, port)
        ret = self._server_process.start()
        if ret:
            print("%s is running" % self._server_process.name())

        print("net socket based video packet reader created, port = %d" % port)

    def read(self):
        try:
            rtp_pkt = self._data_pipe_r.recv()
        except EOFError:  # write pipe connection closed
            print("BUG: write pipe connection should not be closed before reader release")
            return False, None
        except Exception as e:
            print("failed to receive video packet from the pipe: %s" % str(e))
            return False, None

        try:
            self._ack_pipe_w.send("")
        except ValueError as e:
            print("WARN: failed to send ack to the pipe: %s" % str(e))

        return True, rtp_pkt

    def release(self):
        self._server_process.stop();

        self._data_pipe_r.close()
        self._data_pipe_w.close()
        self._ack_pipe_r.close()
        self._ack_pipe_w.close()

        print("net socket based video packet released")
