package com.amazonaws.rp.riverrun.wheeltower.videostreamdemo;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import software.amazon.awscdk.core.Construct;
import software.amazon.awscdk.core.Stack;
import software.amazon.awscdk.core.StackProps;

public class VideoStreamDemoDeviceStack extends Stack {
    private final Logger log = LoggerFactory.getLogger("riverrun-video-stream-demo-device-stack");

    public VideoStreamDemoDeviceStack(final Construct parent, final String id) {
        this(parent, id, null);
    }

    public VideoStreamDemoDeviceStack(final Construct parent, final String id, final StackProps props) {
        super(parent, id, props);

    }
}