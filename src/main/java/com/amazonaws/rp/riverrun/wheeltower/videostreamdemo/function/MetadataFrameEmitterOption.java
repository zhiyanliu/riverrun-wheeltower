package com.amazonaws.rp.riverrun.wheeltower.videostreamdemo.function;

public class MetadataFrameEmitterOption {
    public String getMETADATA_FRAME_SERVER_IP() {
        return "127.0.0.1";
    }

    public String getMETADATA_FRAME_SERVER_PORT() {
        return "9527";
    }

    public String getMETADATA_FRAME_EMIT_TYPE() {
        return "REQ";
    }

    public String getMETADATA_FRAME_REQUEST_RELY_TIMEOUT_MS() {
        return "1000";
    }

    public String getMETADATA_FRAME_PUBLISH_TOPIC() {
        return "md";
    }

    public String getMETADATA_FRAME_NET_SOCKET_SERVER_PORT() {
        return "9525";
    }

    public String getMETADATA_FRAME_INPUT_TYPE() {
        return "HORIZON_SDK";
    }
}
