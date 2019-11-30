package com.amazonaws.rp.riverrun.wheeltower.videostreamdemo;

import org.apache.commons.codec.binary.Base64;
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

    private final String ec2KeyName;
    private final String ec2SetupScriptURLBase64;

    public VideoStreamDemoDeviceStack(final Construct parent, final String id) {
        this(parent, id, null);
    }

    public VideoStreamDemoDeviceStack(final Construct parent, final String id,
                                      final StackProps props) {
        super(parent, id, props);

        Object ec2KeyNameObj = this.getNode().tryGetContext("ec2-key-name");
        if (ec2KeyNameObj == null)
            this.ec2KeyName = null;
        else
            this.ec2KeyName = ec2KeyNameObj.toString();

        Object ec2SetupScriptURLObj = this.getNode().tryGetContext("ec2-setup-script-url-base64");
        if (ec2SetupScriptURLObj == null) {
            this.ec2SetupScriptURLBase64 = null;
        } else {
            String s = ec2SetupScriptURLObj.toString();
            if (!Base64.isBase64(s))
                throw new IllegalArgumentException(
                        "parameter ec2-setup-script-url-base64 is not a valid base64 string");
            this.ec2SetupScriptURLBase64 = s;
        }

        // EC2 instance (act device) stuff
        Vpc vpc = this.createVPC(null);
//        Subnet subnet = this.createSubnet(vpc, igw);
        SecurityGroup sg = this.createSecurityGroup(vpc);
        this.createEC2Device(vpc, sg);
    }

    private Vpc createVPC(CfnInternetGateway igw) {
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
                .description("RiverRun Video Stream demo security group.")
                .allowAllOutbound(true)
                .vpc(vpc)
                .build();

        if (this.ec2KeyName != null) {
            sg.addIngressRule(Peer.anyIpv4(), Port.tcp(22));
        }

        return sg;
    }

    private void createEC2Device(Vpc vpc, SecurityGroup sg) {
        Map<String, List<String>> filters = new HashMap<>();
        filters.put("architecture", Arrays.asList("x86_64"));
        filters.put("image-type", Arrays.asList("machine"));
        filters.put("is-public", Arrays.asList("true"));
        filters.put("state", Arrays.asList("available"));
        filters.put("virtualization-type", Arrays.asList("hvm"));

        LookupMachineImage image = LookupMachineImage.Builder.create()
                .name("*ubuntu-bionic-18.04-amd64-server-*")
                .windows(false)
                // in order to use the image in the AWS Marketplace product,
                // user needs to accept terms and subscribe.
                // To prevent this additional action, we use amazon built-in image only here.
                .owners(Arrays.asList("amazon"))
                .filters(filters)
                .build();

        Instance instance = Instance.Builder.create(this, "rr-video-stream-demo-ec2-device")
                .machineImage(image)
                .instanceType(new InstanceType("t2.small"))
                .vpc(vpc)
                .vpcSubnets(SubnetSelection.builder().subnets(vpc.selectSubnets().getSubnets()).build())
                .securityGroup(sg)
                .keyName(this.ec2KeyName)
                .build();

        if (this.ec2SetupScriptURLBase64 != null) {
            String ec2SetupScriptURL = new String(Base64.decodeBase64(this.ec2SetupScriptURLBase64));

            String cmd = String.format("#!/bin/bash\n" +
                            "sudo apt update\n" +
                            "sudo DEBIAN_FRONTEND=noninteractive apt install -y unzip python3.7 python3.7-dev python3-pip python3-apt build-essential\n" +
                            "sudo ln -sf /usr/bin/python3.7 /usr/bin/python3\n" +
                            "sudo -H pip3 install pyzmq --install-option='--zmq=bundled'\n" +
                            "curl -o /tmp/setup.py -fs '%s'\n" +
                            "python3 /tmp/setup.py\n",
                    ec2SetupScriptURL);
            instance.addUserData(cmd);
        }

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
