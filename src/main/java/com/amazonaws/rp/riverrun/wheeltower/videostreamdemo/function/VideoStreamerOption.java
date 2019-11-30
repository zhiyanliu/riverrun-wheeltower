package com.amazonaws.rp.riverrun.wheeltower.videostreamdemo.function;

public class VideoStreamerOption {
    public String getSYNC_PACKET_SERVER_PORT() {
        return "9529";
    }

    public String getSYNC_PACKET_SERVER_HEARTBEAT_INTERVAL_SEC() {
        return "5";
    }

    public String getRTP_PACKET_FILE_SAVE_PATH() {
        return "/tmp/riverrun-streamer/rtp.dump";
    }

    public String getMETADATA_FRAME_FILE_PATH() {
        return "/tmp/riverrun-streamer/metadata.dump";
    }
}
