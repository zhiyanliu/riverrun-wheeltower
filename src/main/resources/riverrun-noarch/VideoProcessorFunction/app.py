import multiprocessing
import signal
import sys

import process
import server
import sync_policy
import sync_pkt_comm

frame_take_server_process = None
frame_throttle_server_process = None
frame_handle_server_process = None
video_take_server_process = None
sync_pkt_emit_server_process = None
sync_server_process = None

sync_pkt_emit_pipe_r, sync_pkt_emit_pipe_w = multiprocessing.Pipe(False)
frame_handle_pipe_r, frame_handle_pipe_w = multiprocessing.Pipe(False)
frame_throttle_pipe_r, frame_throttle_pipe_w = multiprocessing.Pipe(False)
frame_take_pipe_r, frame_take_pipe_w = multiprocessing.Pipe(False)
video_take_pipe_r, video_take_pipe_w = multiprocessing.Pipe(False)


def signal_handler(sig, frame):
    global frame_take_server_process, frame_throttle_server_process, frame_handle_server_process,\
        video_take_server_process, sync_server_process, sync_pkt_emit_server_process

    print("video processing server signal SIGTERM received")

    if video_take_server_process is not None:
        video_take_server_process.stop()
    if frame_take_server_process is not None:
        frame_take_server_process.stop()
    if frame_throttle_server_process is not None:
        frame_throttle_server_process.stop()
    if frame_handle_server_process is not None:
        frame_handle_server_process.stop()
    if sync_server_process is not None:
        sync_server_process.stop()
    if sync_pkt_emit_server_process is not None:
        sync_pkt_emit_server_process.stop()

    video_take_pipe_r.close()
    video_take_pipe_w.close()
    frame_take_pipe_r.close()
    frame_take_pipe_w.close()
    frame_throttle_pipe_r.close()
    frame_throttle_pipe_w.close()
    frame_handle_pipe_r.close()
    frame_handle_pipe_w.close()
    sync_pkt_emit_pipe_r.close()
    sync_pkt_emit_pipe_w.close()

    print("video processing server exits")
    sys.exit(0)


def server_loop():
    global frame_take_server_process, frame_throttle_server_process, frame_handle_server_process, \
        video_take_server_process, sync_server_process, sync_pkt_emit_server_process

    sync_policy_obj = sync_policy.create_sync_policy()

    sync_pkt_combiner = sync_pkt_comm.create_sync_pkt_combiner()

    sync_pkt_emit_server_process = process.ServerProcess("video stream emitting process",
                                                         server.sync_pkt_emit_server_creator,
                                                         sync_pkt_emit_pipe_r)
    sync_server_process = process.ServerProcess("synchronization process",
                                                server.sync_server_creator,
                                                frame_handle_pipe_r, video_take_pipe_r, sync_pkt_emit_pipe_w,
                                                sync_policy_obj, sync_pkt_combiner)
    frame_handle_server_process = process.ServerProcess("metadata frame handling process",
                                                        server.frame_handle_server_creator, frame_throttle_pipe_r,
                                                        frame_handle_pipe_w)
    frame_throttle_server_process = process.ServerProcess("metadata frame throttling process",
                                                          server.frame_throttle_server_creator, frame_take_pipe_r,
                                                          frame_throttle_pipe_w)
    frame_take_server_process = process.ServerProcess("metadata frame taking process",
                                                      server.frame_take_server_creator, frame_take_pipe_w)
    video_take_server_process = process.ServerProcess("video stream taking process",
                                                      server.video_take_server_creator, video_take_pipe_w)

    ret = sync_pkt_emit_server_process.start()
    if ret:
        print("%s is running" % sync_pkt_emit_server_process.name())
    ret = sync_server_process.start()
    if ret:
        print("%s is running" % sync_server_process.name())
    ret = frame_handle_server_process.start()
    if ret:
        print("%s is running" % frame_handle_server_process.name())
    ret = frame_throttle_server_process.start()
    if ret:
        print("%s is running" % frame_throttle_server_process.name())
    ret = frame_take_server_process.start()
    if ret:
        print("%s is running" % frame_take_server_process.name())
    ret = video_take_server_process.start()
    if ret:
        print("%s is running" % video_take_server_process.name())

    print("video processing server is running")

    sync_pkt_emit_server_process.join()
    sync_server_process.join()
    frame_handle_server_process.join()
    frame_throttle_server_process.join()
    frame_take_server_process.join()
    video_take_server_process.join()


signal.signal(signal.SIGTERM, signal_handler)
server_loop()


def lambda_handler(event, context):
    return
