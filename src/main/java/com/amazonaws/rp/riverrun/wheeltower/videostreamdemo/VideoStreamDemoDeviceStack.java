package com.amazonaws.rp.riverrun.wheeltower.videostreamdemo;

import com.amazonaws.rp.riverrun.wheeltower.utils.S3;
import com.amazonaws.rp.riverrun.wheeltower.utils.StackOutputQuerier;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import software.amazon.awscdk.core.*;
import software.amazon.awscdk.services.ec2.*;

import java.util.Arrays;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

public class VideoStreamDemoDeviceStack extends Stack {
    private final Logger log = LoggerFactory.getLogger("riverrun-video-stream-demo-device-stack");
    private final StackOutputQuerier outputQuerier = new StackOutputQuerier();
    private final S3 s3util = new S3();

    private final String ec2ImageID;
    private final String ec2KeyName;
    private String ec2SetupScriptURL;

    public final static String SETUP_SCRIPT_FILE_NAME = "setup.py";

    public VideoStreamDemoDeviceStack(final Construct parent, final String id,
                                      final String videoStreamDemoGreengrassStackName) {
        this(parent, id, null, videoStreamDemoGreengrassStackName);
    }

    public VideoStreamDemoDeviceStack(final Construct parent, final String id,
                                      final StackProps props, final String videoStreamDemoGreengrassStackName) {
        super(parent, id, props);

        Object ec2DeviceImageIDObj = this.getNode().tryGetContext("ec2-image-id");
        if (ec2DeviceImageIDObj == null)
            // will lookup the Ubuntu 18.04 x86_64 AMI
            this.ec2ImageID = null;
        else
            this.ec2ImageID = ec2DeviceImageIDObj.toString();

        Object ec2KeyNameObj = this.getNode().tryGetContext("ec2-key-name");
        if (ec2KeyNameObj == null)
            this.ec2KeyName = null;
        else
            this.ec2KeyName = ec2KeyNameObj.toString();

        String coreFileBucketName = this.outputQuerier.query(
                this.log, videoStreamDemoGreengrassStackName, "corefilesbucketname");
        if (coreFileBucketName == null)
            // instead of to raise exception, since CDK needs (e.g. list and bootstrap)
            this.ec2SetupScriptURL = null;
        else
            this.ec2SetupScriptURL =
                    this.s3util.getObjectPreSignedUrl(coreFileBucketName, SETUP_SCRIPT_FILE_NAME, 7);

        // EC2 instance (act device) stuff
        Vpc vpc = this.createVPC();
        SecurityGroup sg = this.createSecurityGroup(vpc);
        this.createEC2Device(vpc, sg);
    }

    private Vpc createVPC() {
        // Create a VPC with subnets and a gateway
        SubnetConfiguration subnetConfig = SubnetConfiguration.builder()
                .name("rr-video-stream-demo-subnet")
                .subnetType(SubnetType.PUBLIC)
                .cidrMask(24)
                .build();

        return Vpc.Builder.create(this, "rr-video-stream-demo-vpc")
                .cidr("192.168.0.0/16")
                .enableDnsHostnames(true)
                .enableDnsSupport(true)
                .enableDnsSupport(true)
                .subnetConfiguration(Arrays.asList(subnetConfig))
                .build();
    }

    private SecurityGroup createSecurityGroup(Vpc vpc) {
        SecurityGroup sg = SecurityGroup.Builder.create(this, "rr-video-stream-demo-sg")
                .securityGroupName("rr-video-stream-demo-sg")
                .description("Riverrun Video Stream demo security group.")
                .allowAllOutbound(true)
                .vpc(vpc)
                .build();

        // for PDU input
        sg.addIngressRule(Peer.anyIpv4(), Port.tcp(9525)); // metadata frame
        sg.addIngressRule(Peer.anyIpv4(), Port.tcp(9526)); // video packet

        // for debug
        if (this.ec2KeyName != null) {
            sg.addIngressRule(Peer.anyIpv4(), Port.tcp(22)); // ssh
        }

        return sg;
    }

    private void createEC2Device(Vpc vpc, SecurityGroup sg) {
        IMachineImage image;

        if (this.ec2ImageID == null) {
            Map<String, List<String>> filters = new HashMap<>();
            filters.put("architecture", Arrays.asList("x86_64"));
            filters.put("image-type", Arrays.asList("machine"));
            filters.put("is-public", Arrays.asList("true"));
            filters.put("state", Arrays.asList("available"));
            filters.put("virtualization-type", Arrays.asList("hvm"));

            image = LookupMachineImage.Builder.create()
                    .name("*ubuntu-bionic-18.04-amd64-server-*")
                    .windows(false)
                    // in order to use the image in the AWS Marketplace product,
                    // user needs to accept terms and subscribe.
                    // To prevent this additional action, we use amazon built-in image only here.
                    .owners(Arrays.asList("amazon"))
                    .filters(filters)
                    .build();
        } else {
            Map<String, String> filters = new HashMap<>();
            filters.put(this.getRegion(), this.ec2ImageID);

            image = GenericLinuxImage.Builder.create(filters).build();
        }

        Instance instance = Instance.Builder.create(this, "rr-video-stream-demo-ec2-device")
                .machineImage(image)
                .instanceType(new InstanceType("t2.small"))
                .vpc(vpc)
                .vpcSubnets(SubnetSelection.builder().subnets(vpc.selectSubnets().getSubnets()).build())
                .securityGroup(sg)
                .keyName(this.ec2KeyName)
                .build();

        String cmd = String.format("#!/bin/bash\n" +
                        "sudo apt update\n" +
                        "sudo DEBIAN_FRONTEND=noninteractive apt install -y unzip python3.7 " +
                        "python3.7-dev python3-pip python3-apt build-essential\n" +
                        "sudo ln -sf /usr/bin/python3.7 /usr/bin/python3\n" +
                        "sudo -H pip3 install pyzmq --install-option='--zmq=bundled'\n" +
                        "curl -o /tmp/setup.py -fs '%s'\n" +
                        "python3 /tmp/setup.py\n",
                this.ec2SetupScriptURL);
        instance.addUserData(cmd);

        Tag.add(instance, "Name", "rr-video-stream-demo-device");

        new CfnOutput(this, "ec2-device-id", CfnOutputProps.builder()
                .value(instance.getInstanceId())
                .description("the EC2 instance ID as IoT device for RR video stream demo")
                .build());

        new CfnOutput(this, "ec2-public-ip", CfnOutputProps.builder()
                .value(instance.getInstancePublicIp())
                .description("the EC2 instance public IP as IoT device for RR video stream demo")
                .build());
    }
}
