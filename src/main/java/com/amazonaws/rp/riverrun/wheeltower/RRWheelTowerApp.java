package com.amazonaws.rp.riverrun.wheeltower;

import com.amazonaws.rp.riverrun.wheeltower.videostreamdemo.VideoStreamDemoAssert;
import com.amazonaws.rp.riverrun.wheeltower.videostreamdemo.VideoStreamDemoDeviceStack;
import com.amazonaws.rp.riverrun.wheeltower.videostreamdemo.VideoStreamDemoGreengrassStack;
import com.amazonaws.rp.riverrun.wheeltower.videostreamdemo.VideoStreamDemoIoTStack;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import software.amazon.awscdk.core.App;
import software.amazon.awscdk.core.Environment;
import software.amazon.awscdk.core.StackProps;

public class RRWheelTowerApp {
    private static final Logger log = LoggerFactory.getLogger("riverrun-wheeltower");

    private static final String VIDEO_STREAM_DEMO_IOT_STACK_NAME = "riverrun-video-stream-demo-iot";
    private static final String VIDEO_STREAM_DEMO_GREENGRASS_STACK_NAME = "riverrun-video-stream-demo-greengrass";
    private static final String VIDEO_STREAM_DEMO_DEVICE_STACK_NAME = "riverrun-video-stream-demo-dev";

    public static void main(final String[] argv) throws Exception {
        if (argv.length == 0) {
            App cdkApp = new App();

            // `cdk deploy` follows region config provide by AWSSDK (`~/.aws/config`)
            // `cdk deploy -c KEY=VALUE (array)` to add/overwrite context.
            Object regionObj = cdkApp.getNode().tryGetContext("region");
            String region = null;
            if (regionObj != null)
                region = regionObj.toString();

            StackProps props = StackProps.builder()
                    .withEnv(Environment.builder().withRegion(region).build())
                    .build();
            new VideoStreamDemoIoTStack(cdkApp, VIDEO_STREAM_DEMO_IOT_STACK_NAME, props);
            new VideoStreamDemoGreengrassStack(cdkApp, VIDEO_STREAM_DEMO_GREENGRASS_STACK_NAME, props);
            new VideoStreamDemoDeviceStack(cdkApp, VIDEO_STREAM_DEMO_DEVICE_STACK_NAME, props);

            // required until https://github.com/awslabs/jsii/issues/456 is resolve
            cdkApp.synth();
        } else if ("videostream-demo".equals(argv[0])) {
            try {
                if (argv.length == 2 && "prepare-lambda".equals(argv[1])) {
                    new VideoStreamDemoAssert().provisionLambda(VIDEO_STREAM_DEMO_IOT_STACK_NAME);
                } else if (argv.length == 2 && "cleanup-asset".equals(argv[1])) {
                    new VideoStreamDemoAssert().deProvision(VIDEO_STREAM_DEMO_IOT_STACK_NAME);
                } else {
                    log.error("invalid demo command");
                }
            } catch (Exception e) {
                log.error(e.getMessage());
                System.exit(255);
            }
        } else {
            log.error("invalid parameter, refer document");
            System.exit(2);
        }
    }
}
