import signal
import struct
import sys
import threading
import time

import comm


_stop_flag = False
_latest_read_rtp_pkt = None


def _signal_handler(sig, frame):
    print("signal SIGTERM received")
    global _stop_flag
    stop_flag = True
    time.sleep(2)
    print("video emitter exits")
    sys.exit(0)


def _parse_timestamp(rtp_pkt):
    try:
        timestamp = struct.unpack('!i', rtp_pkt[4:8])[0]
        return True, timestamp
    except Exception as e:
        print("failed to parse RTP packet: %s" % str(e))
        return False, None


def _log_routine():
    _start_log_routine()
    global _latest_read_rtp_pkt
    if _latest_read_rtp_pkt is None:
        return
    ret, timestamp = _parse_timestamp(_latest_read_rtp_pkt)
    if not ret:
        print("invalid RTP packet received")
        return
    print("latest timestamp: %d" % timestamp)


def _start_log_routine():
    log_timer = threading.Timer(5, _log_routine)
    log_timer.start()


def server_loop():
    global _latest_read_rtp_pkt

    reader = comm.create_reader()
    emitter = comm.create_emitter()

    try:
        if reader is None or emitter is None:
            return

        while not _stop_flag:
            ret, rtp_pkt = reader.read()
            if not ret:
                continue

            if len(rtp_pkt) > 0:
                _latest_read_rtp_pkt = rtp_pkt
                # send the video RTP packet to the process server
                emitter.emit(rtp_pkt)
            else:
                print("WARN: read an emtpy RTP packet, ignored")
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
