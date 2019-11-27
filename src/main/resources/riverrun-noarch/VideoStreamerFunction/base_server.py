import multiprocessing
import multiprocessing.queues
import threading


class Server:
    def __init__(self, name, stat_queue, log_interval_sec=5):
        self._name = name
        self._stop_flag = multiprocessing.Event()
        self._stat_queue = stat_queue
        self._log_interval = log_interval_sec
        self._start_log_routine()

    def _start_log_routine(self):
        self._log_timer = threading.Timer(self._log_interval, self._log_routine)
        self._log_timer.start()

    def _log_routine(self):
        pass

    def _report_stat(self, *args):
        if self._stat_queue is not None:
            try:
                self._stat_queue.put_nowait(args)
            except multiprocessing.queues.Full:
                pass

    def name(self):
        return self._name

    def stop(self):
        self._stop_flag.set()

    def release(self):
        self._log_timer.cancel()
