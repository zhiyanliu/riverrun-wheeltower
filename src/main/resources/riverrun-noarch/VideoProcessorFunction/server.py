import emit_server
import frame_handle_server
import frame_throttle_server
import sync_server
import take_server


def sync_pkt_emit_server_creator(sync_pkt_emit_pipe_r):
    return emit_server.SyncPacketEmitServer("synchronized packet emitting server", sync_pkt_emit_pipe_r)


def sync_server_creator(frame_handle_pipe_r, video_take_pipe_r, sync_pkt_emit_pipe_w,
                        sync_policy, sync_pkt_combiner):
    return sync_server.SyncServer("synchronization server", frame_handle_pipe_r, video_take_pipe_r,
                                  sync_pkt_emit_pipe_w, sync_policy, sync_pkt_combiner)


def frame_handle_server_creator(frame_throttle_pipe_r, frame_handle_pipe_w):
    return frame_handle_server.FrameHandleServer("metadata frame handling server",
                                                 frame_throttle_pipe_r, frame_handle_pipe_w)


def frame_throttle_server_creator(frame_take_pipe_r, frame_throttle_pipe_w):
    return frame_throttle_server.FrameThrottleServer("metadata frame throttling server",
                                                     frame_take_pipe_r, frame_throttle_pipe_w)


def frame_take_server_creator(frame_take_pipe_w):
    return take_server.FrameTakeServer("metadata frame taking server", frame_take_pipe_w)


def video_take_server_creator(video_take_pipe_w):
    return take_server.VideoTakeServer("video stream taking server", video_take_pipe_w)
