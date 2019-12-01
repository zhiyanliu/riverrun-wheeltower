package com.amazonaws.rp.riverrun.wheeltower.videostreamdemo.function;

public class VideoProcessorOption {
    public final String METADATA_FRAME_SERVER_PORT = "9527";
    public final String METADATA_FRAME_TAKE_TYPE = "REP";
    public final String METADATA_FRAME_SUBSCRIBE_TOPIC = "md";
    public final String VIDEO_STREAM_SERVER_PORT = "9528";
    public final String VIDEO_STREAM_TAKE_TYPE = "REP";
    public final String VIDEO_STREAM_SUBSCRIBE_TOPIC = "rtp";
    public final String SYNC_PACKET_POLICY_TYPE = "ONE_SHOT";
    public final String SYNC_PACKET_POLICY_QUEUE_SIZE = "15";
    public final String SYNC_PACKET_POLICY_SEND_METADATA_FRAME_ONCE = "YES";
    public final String SYNC_PACKET_SERVER_IP = "127.0.0.1";  // 52.80.220.189, GUI in innovation center
    public final String SYNC_PACKET_SERVER_PORT = "9529";  // 19998, GUI in innovation center
    public final String SYNC_PACKET_SERVER_HEARTBEAT_TIMEOUT_SEC = "5";
    public final String METADATA_FRAME_THROTTLE_TOLERATE_COUNT = "0";
}
