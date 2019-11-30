package com.amazonaws.rp.riverrun.wheeltower.videostreamdemo.function;

public class VideoEmitterOption {
    public String getVIDEO_STREAM_SERVER_IP() {
        return "127.0.0.1";
    }

    public String getVIDEO_STREAM_SERVER_PORT() {
        return "9528";
    }

    public String getVIDEO_STREAM_EMIT_TYPE() {
        return "REQ";
    }

    public String getVIDEO_STREAM_REQUEST_RELY_TIMEOUT_MS() {
        return "1000";
    }

    public String getVIDEO_STREAM_PUBLISH_TOPIC() {
        return "rtp";
    }

    public String getVIDEO_RTP_PACKET_SHM_FILENAME() {
        return "foo_30M";
    }

    public String getVIDEO_RTP_PACKET_NET_SOCKET_SERVER_PORT() {
        return "9526";
    }

    public String getVIDEO_RTP_PACKET_INPUT_TYPE() {
        return "HORIZON_SDK";
    }
}
