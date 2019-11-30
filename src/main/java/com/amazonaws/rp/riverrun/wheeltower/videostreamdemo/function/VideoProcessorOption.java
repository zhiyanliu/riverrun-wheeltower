package com.amazonaws.rp.riverrun.wheeltower.videostreamdemo.function;

public class VideoProcessorOption {
    public String getMETADATA_FRAME_SERVER_PORT() {
        return "9527";
    }

    public String getMETADATA_FRAME_TAKE_TYPE() {
        return "REP";
    }

    public String getMETADATA_FRAME_SUBSCRIBE_TOPIC() {
        return "md";
    }

    public String getVIDEO_STREAM_SERVER_PORT() {
        return "9528";
    }

    public String getVIDEO_STREAM_TAKE_TYPE() {
        return "REP";
    }

    public String getVIDEO_STREAM_SUBSCRIBE_TOPIC() {
        return "rtp";
    }

    public String getSYNC_PACKET_POLICY_TYPE() {
        return "ONE_SHOT";
    }

    public String getSYNC_PACKET_POLICY_QUEUE_SIZE() {
        return "15";
    }

    public String getSYNC_PACKET_POLICY_SEND_METADATA_FRAME_ONCE() {
        return "YES";
    }

    public String getSYNC_PACKET_SERVER_IP() {
        return "127.0.0.1";  // 52.80.220.189, GUI in innovation center
    }

    public String getSYNC_PACKET_SERVER_PORT() {
        return "9529";  // 19998, GUI in innovation center
    }

    public String getSYNC_PACKET_SERVER_HEARTBEAT_TIMEOUT_SEC() {
        return "5";
    }

    public String getMETADATA_FRAME_THROTTLE_TOLERATE_COUNT() {
        return "0";
    }
}
