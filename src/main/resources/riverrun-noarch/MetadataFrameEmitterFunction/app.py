import signal
import sys
import threading
import time

import comm


_stop_flag = False
_latest_read_count = 0


def _signal_handler(sig, frame):
    print("signal SIGTERM received")
    global _stop_flag
    _stop_flag = True
    time.sleep(2)
    print("metadata frame emitter exits")
    sys.exit(0)


def _log_routine():
    _start_log_routine()
    global _latest_read_count
    print("read %d metadata frames" % _latest_read_count)


def _start_log_routine():
    log_timer = threading.Timer(5, _log_routine)
    log_timer.start()


def server_loop():
    global _latest_read_count

    reader = comm.create_reader()
    emitter = comm.create_emitter()

    try:
        if reader is None or emitter is None:
            return

        while not _stop_flag:
            ret, meta_frame_timestamp, meta_frame_buff = reader.read()
            if not ret:
                continue

            if len(meta_frame_buff) > 0:
                _latest_read_count += 1
                # send the metadata frame data to the process server
                emitter.emit(meta_frame_timestamp, meta_frame_buff)
            else:
                print("WARN: read an emtpy metadata frame, ignored")
    finally:
        if reader is not None:
            try:
                reader.release()
            except Exception as e:
                print(str(e))
        if emitter is not None:
            try:
                emitter.release()
            except Exception as e:
                print(str(e))


signal.signal(signal.SIGTERM, _signal_handler)

_start_log_routine()
server_loop()


def lambda_handler(event, context):
    return
