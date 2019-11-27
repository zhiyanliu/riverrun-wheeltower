package com.amazonaws.rp.riverrun.wheeltower.videostreamdemo;

import com.amazonaws.rp.riverrun.wheeltower.utils.StackOutputQuerier;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.IOException;

public class VideoStreamDemoAssert {
    private final Logger log = LoggerFactory.getLogger("riverrun-video-stream-demo-asset");
    private final StackOutputQuerier outputQuerier = new StackOutputQuerier();

    private final static String PUB_KEY_NAME = "rr-video-stream-demo-greengrass-core-thing-public";
    private final static String PRV_KEY_NAME = "rr-video-stream-demo-greengrass-core-thing-private";
    private final static String ROOT_CA_NAME = "root-ca.crt";

    private final static String CREDENTIALS_FILE_NAME = "credentials.zip";
    private final static String GG_CORE_CONFIG_FILE_NAME = "rr-video-stream-demo-greengrass-core-config.json";
    private final static String SETUP_SCRIPT_FILE_NAME = "setup.py";


    public void provision(final String videoStreamDemoGreengrassStackName) throws IOException {
        String coreFileBucketName = this.queryCoreFileBucketName(videoStreamDemoGreengrassStackName);
        if (coreFileBucketName == null)
            throw new IllegalArgumentException(String.format(
                    "the name of s3 bucket to save greengrass core assert files not found, " +
                            "is the RR video streamer demo stack %s invalid?", videoStreamDemoGreengrassStackName));
    }

    public void deProvision(final String videoStreamDemoGreengrassStackName) throws IOException {

    }

    private String queryCoreFileBucketName(String videoStreamDemoIoTStackName) {
        return this.outputQuerier.query(videoStreamDemoIoTStackName, "corefilesbucketname");
    }
}
