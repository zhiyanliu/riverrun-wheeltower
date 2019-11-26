package com.amazonaws.rp.riverrun.wheeltower.videostreamdemo;

import com.amazonaws.rp.riverrun.wheeltower.utils.StackOutputQuerier;
import com.google.common.collect.Lists;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import software.amazon.awscdk.core.*;
import software.amazon.awscdk.services.greengrass.*;
import software.amazon.awscdk.services.iam.ManagedPolicy;
import software.amazon.awscdk.services.iam.Role;
import software.amazon.awscdk.services.iam.RoleProps;
import software.amazon.awscdk.services.iam.ServicePrincipal;

import java.io.IOException;
import java.util.Arrays;

public class VideoStreamDemoGreengrassStack extends Stack {
    private final Logger log = LoggerFactory.getLogger("riverrun-video-stream-demo-greengrass-stack");
    private final StackOutputQuerier outputQuerier = new StackOutputQuerier();

    private final static String LAMBDA_FUNC_ROLE_NAME = "rr-video-stream-demo-lambda-func-role";

    private final static String GG_GROUP_ROLE_NAME = "rr-video-stream-demo-greengrass-group-role";
    private final static String GG_GROUP_NAME = "rr-video-stream-demo";
    private final static String GG_CROUP_VER_NAME = "rr-video-stream-demo-v0";
    private final static String GG_CORE_NAME = "rr-video-stream-demo-core";
    private final static String GG_CORE_VER_NAME = "rr-video-stream-demo-core-v0";

    private final String coreFileBucketName;
    private final String certArn;
    private final String thingName;
    private final String thingArn;

    public VideoStreamDemoGreengrassStack(final Construct parent, final String id) throws IOException {
        this(parent, id, null);
    }

    public VideoStreamDemoGreengrassStack(final Construct parent, final String id,
                                          final StackProps props) throws IOException {
        super(parent, id, props);

        Object coreFileBucketNameObj = this.getNode().tryGetContext("core-files-bucket-name");
        if (coreFileBucketNameObj == null)
            this.coreFileBucketName = "";
        else
            this.coreFileBucketName = coreFileBucketNameObj.toString();

        Object certArnObj = this.getNode().tryGetContext("thing-cert-arn");
        if (certArnObj == null)
            this.certArn = "";
        else
            this.certArn = certArnObj.toString();

        Object thingNameObj = this.getNode().tryGetContext("thing-name");
        if (thingNameObj == null)
            this.thingName = "";
        else
            this.thingName = thingNameObj.toString();

        Object thingArnObj = this.getNode().tryGetContext("thing-arn");
        if (thingArnObj == null)
            this.thingArn = "";
        else
            this.thingArn = thingArnObj.toString();

        // Lambda stuff
        Role lambdaFuncRole = this.createLambdaFunctionRole();

        // IoT Greengrass stuff
        Role ggGroupRole = this.createGreengressGroupRole();
        CfnCoreDefinitionVersion coreVersion = this.createGreengrassCore(certArn, thingName, thingArn);
        this.createGreengrassGroup(ggGroupRole, coreVersion);
    }

    private Role createLambdaFunctionRole() {
        // Create an IAM role for the lambda function
        Role lambdaFuncRole = new Role(this, LAMBDA_FUNC_ROLE_NAME, RoleProps.builder()
                .withAssumedBy(new ServicePrincipal("lambda.amazonaws.com"))
                .withManagedPolicies(Lists.newArrayList(
                        ManagedPolicy.fromAwsManagedPolicyName("AWSLambdaBasicExecutionRole")))
                .build());

        new CfnOutput(this, "lambda-function-iam-role-arn", CfnOutputProps.builder()
                .withValue(lambdaFuncRole.getRoleArn())
                .withDescription("the Greengrass group role ARN for RR video stream demo")
                .build());

        return lambdaFuncRole;
    }

    private Role createGreengressGroupRole() {
        // Create an IAM role for the greengrass group
        Role ggGroupRole = new Role(this, GG_GROUP_ROLE_NAME, RoleProps.builder()
                .withAssumedBy(new ServicePrincipal("greengrass.amazonaws.com"))
                .withManagedPolicies(Lists.newArrayList(
                        ManagedPolicy.fromAwsManagedPolicyName("AWSLambdaFullAccess")))
                .build());

        new CfnOutput(this, "greengrass-group-iam-role-arn", CfnOutputProps.builder()
                .withValue(ggGroupRole.getRoleArn())
                .withDescription("the Greengrass group role ARN for RR video stream demo")
                .build());

        return ggGroupRole;
    }

    private CfnCoreDefinitionVersion createGreengrassCore(String certArn, String thingID, String thingArn) {
        CfnCoreDefinition coreDefinition = new CfnCoreDefinition(this, GG_CORE_NAME,
                CfnCoreDefinitionProps.builder()
                        .withName(GG_CORE_NAME)
                        .build());

        CfnCoreDefinitionVersion.CoreProperty coreProperty = new CfnCoreDefinitionVersion.CoreProperty() {
            @Override
            public String getCertificateArn() {
                return certArn;
            }

            @Override
            public String getId() {
                return thingID;
            }

            @Override
            public String getThingArn() {
                return thingArn;
            }

            @Override
            public Object getSyncShadow() {
                return Boolean.FALSE;
            }
        };

        CfnCoreDefinitionVersion coreVersion = new CfnCoreDefinitionVersion(this, GG_CORE_VER_NAME,
                CfnCoreDefinitionVersionProps.builder()
                        .withCoreDefinitionId(coreDefinition.getRef())
                        .withCores(Arrays.asList(coreProperty))
                        .build());

        return coreVersion;
    }

    private CfnGroup createGreengrassGroup(Role ggGroupRole, CfnCoreDefinitionVersion coreVersion) {
        CfnGroup group = new CfnGroup(this, GG_GROUP_NAME, CfnGroupProps.builder()
                .withName(GG_GROUP_NAME)
                .withRoleArn(ggGroupRole.getRoleArn())
                .build());

        new CfnGroupVersion(this, GG_CROUP_VER_NAME, CfnGroupVersionProps.builder()
                .withGroupId(group.getRef())
                .withCoreDefinitionVersionArn(coreVersion.getRef())
                .build());

        return group;
    }
}
