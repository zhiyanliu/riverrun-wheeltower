package com.amazonaws.rp.riverrun.wheeltower.videostreamdemo;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import software.amazon.awscdk.core.Construct;
import software.amazon.awscdk.core.Stack;
import software.amazon.awscdk.core.StackProps;

import java.io.IOException;

public class VideoStreamDemoGreengrassStack extends Stack {
    private final Logger log = LoggerFactory.getLogger("riverrun-video-stream-demo-greengrass-stack");

    public VideoStreamDemoGreengrassStack(final Construct parent, final String id) throws IOException {
        this(parent, id, null);
    }

    public VideoStreamDemoGreengrassStack(final Construct parent, final String id,
                                          final StackProps props) throws IOException {
        super(parent, id, props);


    }
}
