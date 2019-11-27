import multiprocessing
import signal
import sys

import comm


sync_pkt_receiver = None


def signal_handler(sig, frame):
    global sync_pkt_receiver

    print("video stream server signal SIGTERM received")

    if sync_pkt_receiver is not None:
        sync_pkt_receiver.shutdown()
        sync_pkt_receiver.release()

    print("video stream server exits")
    sys.exit(0)


def server_loop():
    global sync_pkt_receiver

    stat_queue = multiprocessing.Queue(5)

    sync_pkt_receiver = comm.create_sync_pkt_receiver(stat_queue)
    print("synchronized packet TCP receiver is running")

    print("video streaming server is running")
    sync_pkt_receiver.run()


signal.signal(signal.SIGTERM, signal_handler)
server_loop()


def lambda_handler(event, context):
    return
