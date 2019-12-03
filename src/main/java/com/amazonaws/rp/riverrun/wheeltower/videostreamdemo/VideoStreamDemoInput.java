package com.amazonaws.rp.riverrun.wheeltower.videostreamdemo;

import com.amazonaws.rp.riverrun.wheeltower.utils.StackOutputQuerier;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.IOException;
import java.util.concurrent.atomic.AtomicInteger;

public class VideoStreamDemoInput {
    private final Logger log = LoggerFactory.getLogger("riverrun-video-stream-demo-intput");
    private final StackOutputQuerier outputQuerier = new StackOutputQuerier();

    public void send(final String videoStreamDemoDeviceStackName) throws IOException {
        String ip = this.outputQuerier.query(this.log, videoStreamDemoDeviceStackName, "ec2publicip");
        if (ip == null)
            throw new IllegalArgumentException(String.format(
                    "the public IP of EC2 instance as IoT device not found, " +
                            "is the RR video streamer demo stack %s invalid?", videoStreamDemoDeviceStackName));

        this.sendTo(ip);
    }

    public void sendTo(final String ip) throws IOException {
        SendThread videoPacketSender = null;
        SendThread metadataSender = null;

        try {
            String videoDumpFilePath = String.format(
                    "%s/src/main/resources/rr-video-stream-demo/video_packet.dump",
                    System.getProperty("user.dir"));
            String metadataDumpFilePath = String.format(
                    "%s/src/main/resources/rr-video-stream-demo/metadata_frame.dump",
                    System.getProperty("user.dir"));

            int port1 = 9526, port2 = 9525;

            AtomicInteger videoPacketTimestampWatermark = new AtomicInteger(-1);

            videoPacketSender = new VideoPacketSendThread(
                    "video packet sender", this.log, videoDumpFilePath, ip, port1, videoPacketTimestampWatermark);
            metadataSender = new MetadataFrameSendThread(
                    "metadata frame sender", this.log, metadataDumpFilePath, ip, port2, videoPacketTimestampWatermark);

            videoPacketSender.start();
            log.info(String.format("start to send video packet to the device %s:%d...", ip, port1));
            metadataSender.start();
            log.info(String.format("start to send metadata frame to the device %s:%d...", ip, port2));

            try {
                videoPacketSender.join();
                metadataSender.join();
            } catch (InterruptedException e) {
                log.info(String.format("data sending is interrupted: ", e.getMessage()));
            }

            log.info("all demo data are sent, exits");
        } finally {
            if (videoPacketSender != null)
                videoPacketSender.close();

            if (metadataSender != null)
                metadataSender.close();
        }
    }
}
