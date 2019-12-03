package com.amazonaws.rp.riverrun.wheeltower;

import com.amazonaws.regions.DefaultAwsRegionProviderChain;
import com.amazonaws.rp.riverrun.wheeltower.videostreamdemo.VideoStreamDemoAssert;
import com.amazonaws.rp.riverrun.wheeltower.videostreamdemo.VideoStreamDemoDeviceStack;
import com.amazonaws.rp.riverrun.wheeltower.videostreamdemo.VideoStreamDemoGreengrassStack;
import com.amazonaws.rp.riverrun.wheeltower.videostreamdemo.VideoStreamDemoInput;
import com.amazonaws.services.securitytoken.AWSSecurityTokenService;
import com.amazonaws.services.securitytoken.AWSSecurityTokenServiceClientBuilder;
import com.amazonaws.services.securitytoken.model.GetCallerIdentityRequest;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import software.amazon.awscdk.core.App;
import software.amazon.awscdk.core.Environment;
import software.amazon.awscdk.core.StackProps;

public class RRWheelTowerApp {
    private static final Logger log = LoggerFactory.getLogger("riverrun-wheeltower");

    private static final String VIDEO_STREAM_DEMO_GREENGRASS_STACK_NAME = "riverrun-video-stream-demo-greengrass";
    private static final String VIDEO_STREAM_DEMO_DEVICE_STACK_NAME = "riverrun-video-stream-demo-dev";

    public static void main(final String[] argv) throws Exception {
        String region, account;

        // makes `cdk deploy` to follow region config provide by AWSSDK (`~/.aws/config`)
        // or use the environment variables "CDK_DEFAULT_ACCOUNT" and "CDK_DEFAULT_REGION"
        //  to inherit environment information from the CLI
        if (System.getenv().containsKey("CDK_DEFAULT_REGION")) {
            region = System.getenv().get("CDK_DEFAULT_REGION");
        } else {
            region = new DefaultAwsRegionProviderChain().getRegion();
        }
        if (System.getenv().containsKey("CDK_DEFAULT_ACCOUNT")) {
            account = System.getenv().get("CDK_DEFAULT_ACCOUNT");
        } else {
            AWSSecurityTokenService stsClient = AWSSecurityTokenServiceClientBuilder.defaultClient();
            account = stsClient.getCallerIdentity(new GetCallerIdentityRequest()).getAccount();
        }

        if (argv.length == 0) {
            StackProps props = StackProps.builder()
                    .env(Environment.builder()
                            .region(region)
                            .account(account)
                            .build())
                    .build();

            App cdkApp = App.Builder.create().build();

            new VideoStreamDemoGreengrassStack(cdkApp, VIDEO_STREAM_DEMO_GREENGRASS_STACK_NAME, props);
            new VideoStreamDemoDeviceStack(cdkApp, VIDEO_STREAM_DEMO_DEVICE_STACK_NAME, props,
                    VIDEO_STREAM_DEMO_GREENGRASS_STACK_NAME);

            // required until https://github.com/awslabs/jsii/issues/456 is resolve
            cdkApp.synth();
        } else if ("videostream-demo".equals(argv[0])) {
            try {
                VideoStreamDemoAssert demoAssert = new VideoStreamDemoAssert(region);
                VideoStreamDemoInput input = new VideoStreamDemoInput();

                if (argv.length == 2 && "prepare-asset".equals(argv[1])) {
                    demoAssert.provision(VIDEO_STREAM_DEMO_GREENGRASS_STACK_NAME);
                } else if (argv.length == 2 && "cleanup-asset".equals(argv[1])) {
                    demoAssert.deProvision(VIDEO_STREAM_DEMO_GREENGRASS_STACK_NAME);
                } else if (argv.length == 2 && "deploy-app".equals(argv[1])) {
                    demoAssert.deployApp(VIDEO_STREAM_DEMO_GREENGRASS_STACK_NAME);
                } else if (argv.length == 2 && "send-data".equals(argv[1])) {
                    input.send(VIDEO_STREAM_DEMO_DEVICE_STACK_NAME); // query device ip from stack outputs
                } else if (argv.length == 3 && "send-data".equals(argv[1])) {
                    input.sendTo(argv[2]); // use own device
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
