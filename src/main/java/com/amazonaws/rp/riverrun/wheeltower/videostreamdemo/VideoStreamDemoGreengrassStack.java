package com.amazonaws.rp.riverrun.wheeltower.videostreamdemo;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.SerializationFeature;
import com.google.common.collect.Lists;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import software.amazon.awscdk.core.Stack;
import software.amazon.awscdk.core.*;
import software.amazon.awscdk.services.greengrass.*;
import software.amazon.awscdk.services.iam.ManagedPolicy;
import software.amazon.awscdk.services.iam.Role;
import software.amazon.awscdk.services.iam.ServicePrincipal;
import software.amazon.awscdk.services.iot.*;
import software.amazon.awscdk.services.lambda.Code;
import software.amazon.awscdk.services.lambda.Function;
import software.amazon.awscdk.services.lambda.Runtime;
import software.amazon.awscdk.services.lambda.Version;
import software.amazon.awscdk.services.s3.BlockPublicAccess;
import software.amazon.awscdk.services.s3.BlockPublicAccessOptions;
import software.amazon.awscdk.services.s3.Bucket;

import javax.annotation.Nullable;
import java.io.IOException;
import java.net.URL;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.*;

public class VideoStreamDemoGreengrassStack extends Stack {
    private final Logger log = LoggerFactory.getLogger("riverrun-video-stream-demo-greengrass-stack");

    private final static ObjectMapper JSON =
            new ObjectMapper().configure(SerializationFeature.INDENT_OUTPUT, true);

    private final static String POLICY_NAME = "rr-video-stream-demo-greengrass-core-thing-policy";
    private final static String THING_NAME = "rr-video-stream-demo-greengrass-core-thing";
    private final static String CSR_NAME = "rr-video-stream-demo-greengrass-core-thing-csr";
    private final static String CERT_NAME = "rr-video-stream-demo-greengrass-core-thing-cert";

    private final static String CORE_FILE_BUCKET_NAME = "rr-video-stream-demo-core-files";

    private final static String LAMBDA_FUNC_ROLE_NAME = "rr-video-stream-demo-lambda-func-role";
    private final static String METADATA_FRAME_EMITTER_FUNC_NAME = "rr-video-stream-demo-MetadataFrameEmitter";
    private final static String VIDEO_EMITTER_FUNC_NAME = "rr-video-stream-demo-VideoEmitter";
    private final static String VIDEO_PROCESSOR_FUNC_NAME = "rr-video-stream-demo-VideoProcessor";
    private final static String VIDEO_STREAMER_FUNC_NAME = "rr-video-stream-demo-VideoStreamer";
    private final static String METADATA_FRAME_EMITTER_FUNC_DIR_NAME = "MetadataFrameEmitterFunction";
    private final static String VIDEO_EMITTER_FUNC_DIR_NAME = "VideoEmitterFunction";
    private final static String VIDEO_PROCESSOR_FUNC_DIR_NAME = "VideoProcessorFunction";
    private final static String VIDEO_STREAMER_FUNC_DIR_NAME = "VideoStreamerFunction";

    private final static String GG_GROUP_ROLE_NAME = "rr-video-stream-demo-greengrass-group-role";
    private final static String GG_GROUP_NAME = "rr-video-stream-demo";
    private final static String GG_CROUP_VER_NAME = "rr-video-stream-demo-v0";
    private final static String GG_CORE_NAME = "rr-video-stream-demo-core";
    private final static String GG_CORE_VER_NAME = "rr-video-stream-demo-core-v0";
    private final static String GG_FUNCTION_NAME = "rr-video-stream-demo-lambda";
    private final static String GG_FUNCTION_VER_NAME = "rr-video-stream-demo-lambda-v0";

    private final String coreFileBucketName;

    public VideoStreamDemoGreengrassStack(final Construct parent, final String id) throws IOException {
        this(parent, id, null);
    }

    public VideoStreamDemoGreengrassStack(final Construct parent, final String id,
                                          final StackProps props) throws IOException {
        super(parent, id, props);

        Random rand = new Random();
        this.coreFileBucketName = String.format("%s-%d", CORE_FILE_BUCKET_NAME, Math.abs(rand.nextLong()));

        List<String> functionNames = Arrays.asList(
                METADATA_FRAME_EMITTER_FUNC_NAME, VIDEO_EMITTER_FUNC_NAME,
                VIDEO_PROCESSOR_FUNC_NAME, VIDEO_STREAMER_FUNC_NAME);

        // IoT thing stuff
        CfnPolicy policy = this.createThingPolicy();
        CfnThing thing = this.createThing();
        CfnCertificate cert = this.createThingCert(policy, thing);
        this.createCoreFileS3Bucket();

        // Lambda stuff
        Role lambdaFuncRole = this.createLambdaFunctionRole();
        List<Function> functions = this.createLambdaFunctions(lambdaFuncRole, functionNames);
        List<Version> functionVersions = this.createLambdaFunctionVersions(functions, functionNames);

        // IoT Greengrass stuff
        Role ggGroupRole = this.createGreengressGroupRole();
        CfnCoreDefinitionVersion coreVersion = this.createGreengrassCore(cert, thing);
        CfnFunctionDefinitionVersion iotFunctionVersion = this.createGreengrassFunctionVersion(functionVersions);
        this.createGreengrassGroup(ggGroupRole, coreVersion, iotFunctionVersion);
    }

    private CfnPolicy createThingPolicy() throws IOException {
        // Create a policy
        String fileName = String.format("rr-video-stream-demo/%s.json", POLICY_NAME);
        URL inlinePolicyDoc = getClass().getClassLoader().getResource(fileName);
        if (inlinePolicyDoc == null)
            throw new IllegalArgumentException(String.format("the policy statement file %s not found", fileName));
        JsonNode node = JSON.readTree(inlinePolicyDoc);

        CfnPolicy policy = CfnPolicy.Builder.create(this, POLICY_NAME)
                .policyName(POLICY_NAME)
                .policyDocument(node)
                .build();

        // Output the policy configuration
        CfnOutput.Builder.create(this, "policy-name")
                .value(Objects.requireNonNull(policy.getPolicyName()))
                .description("the policy name for RR video stream demo")
                .build();

        CfnOutput.Builder.create(this, "policy-arn")
                .value(policy.getAttrArn())
                .description("the policy arn for RR video stream demo")
                .build();

        return policy;
    }

    private CfnThing createThing() {
        // Create a thing
        CfnThing thing = CfnThing.Builder.create(this, THING_NAME)
                .thingName(THING_NAME)
                .build();

        // Output the thing configuration
        CfnOutput.Builder.create(this, "thing-name")
                .value(Objects.requireNonNull(thing.getThingName()))
                .description("the thing name for RR video stream demo")
                .build();

        return thing;
    }

    private CfnCertificate createThingCert(CfnPolicy policy, CfnThing thing) throws IOException {
        // Load CSR
        String fileName = String.format("rr-video-stream-demo/%s.pem", CSR_NAME);
        URL inlineCSRPem = getClass().getClassLoader().getResource(fileName);
        if (inlineCSRPem == null)
            throw new IllegalArgumentException(String.format("CSR file %s not found", fileName));
        String csrPem = new String(inlineCSRPem.openStream().readAllBytes());

        // Create a certificate
        CfnCertificate cert = CfnCertificate.Builder.create(this, CERT_NAME)
                .certificateSigningRequest(csrPem)
                .status("ACTIVE")
                .build();

        cert.addDependsOn(policy);
        cert.addDependsOn(thing);

        // Attach the policy to the certificate
        CfnPolicyPrincipalAttachment.Builder.create(this, "rr-video-stream-demo-policy2cert")
                .policyName(POLICY_NAME)
                .principal(cert.getAttrArn())
                .build();

        // Attach the certificate to the thing
        CfnThingPrincipalAttachment.Builder.create(this, "rr-video-stream-demo-cert2thing")
                .thingName(THING_NAME)
                .principal(cert.getAttrArn())
                .build();

        // Output the thing configuration
        CfnOutput.Builder.create(this, "cert-id")
                .value(cert.getRef())
                .description("the thing certificate ID for RR video stream demo")
                .build();

        CfnOutput.Builder.create(this, "cert-arn")
                .value(cert.getAttrArn())
                .description("the thing certificate ARN for RR video stream demo")
                .build();

        return cert;
    }

    private void createCoreFileS3Bucket() {
        Bucket coreFileBucket = Bucket.Builder.create(this, this.coreFileBucketName)
                .blockPublicAccess(new BlockPublicAccess(BlockPublicAccessOptions.builder()
                        .blockPublicAcls(false)
                        .blockPublicPolicy(true)
                        .restrictPublicBuckets(true)
                        .build()))
                .removalPolicy(RemovalPolicy.DESTROY)
                .publicReadAccess(false)
                .bucketName(this.coreFileBucketName)
                .build();

        CfnOutput.Builder.create(this, "core-files-bucket-name")
                .value(coreFileBucket.getBucketName())
                .description("the name of s3 bucket to save greengrass core assert files " +
                        "to act IoT device for RR video stream demo")
                .build();
    }

    private Role createLambdaFunctionRole() {
        // Create an IAM role for the lambda function
        Role lambdaFuncRole = Role.Builder.create(this, LAMBDA_FUNC_ROLE_NAME)
                .assumedBy(new ServicePrincipal("lambda.amazonaws.com"))
                .managedPolicies(Lists.newArrayList(
                        ManagedPolicy.fromAwsManagedPolicyName("service-role/AWSLambdaBasicExecutionRole")))
                .build();

        CfnOutput.Builder.create(this, "lambda-function-iam-role-arn")
                .value(lambdaFuncRole.getRoleArn())
                .description("the Greengrass group role ARN for RR video stream demo")
                .build();

        return lambdaFuncRole;
    }

    private Function createLambdaFunction(Role lambdaFuncRole,
                                          String functionName, String functionSourceDirName) {

        Path currentPath = Paths.get(System.getProperty("user.dir"));
        Path functionSourceDirPath = Paths.get(currentPath.toString(),
                "src/main/resources/riverrun-noarch", functionSourceDirName);

        Function function = Function.Builder.create(this, functionName)
                .runtime(Runtime.PYTHON_3_7)
                .code(Code.fromAsset(functionSourceDirPath.toString()))
                .functionName(functionName)
                .handler("app.lambda_handler")
                .role(lambdaFuncRole)
                .build();

        return function;
    }

    private List<Function> createLambdaFunctions(Role lambdaFuncRole, List<String> functionNames) {
        List<String> functionSourceDirNames = Arrays.asList(
                METADATA_FRAME_EMITTER_FUNC_DIR_NAME, VIDEO_EMITTER_FUNC_DIR_NAME,
                VIDEO_PROCESSOR_FUNC_DIR_NAME, VIDEO_STREAMER_FUNC_DIR_NAME);

        List<Function> functions = new ArrayList<>(functionSourceDirNames.size());

        for (int i = 0; i < functionNames.size(); i++) {
            Function function = this.createLambdaFunction(
                    lambdaFuncRole, functionNames.get(i), functionSourceDirNames.get(i));
            functions.add(function);
        }

        return functions;
    }

    private List<Version> createLambdaFunctionVersions(List<Function> functions, List<String> functionNames) {
        List<Version> functionVersions = new ArrayList<>(functions.size());

        for (int i = 0; i < functionNames.size(); i++) {
            Version functionVersion = Version.Builder.create(this, String.format("%s-v1", functionNames.get(i)))
                    .lambda(functions.get(i))
                    .build();
            functionVersions.add(functionVersion);
        }

        return functionVersions;
    }

    private Role createGreengressGroupRole() {
        // Create an IAM role for the greengrass group
        Role ggGroupRole = Role.Builder.create(this, GG_GROUP_ROLE_NAME)
                .assumedBy(new ServicePrincipal("greengrass.amazonaws.com"))
                .managedPolicies(Lists.newArrayList(
                        ManagedPolicy.fromAwsManagedPolicyName("AWSLambdaFullAccess")))
                .build();

        CfnOutput.Builder.create(this, "greengrass-group-iam-role-arn")
                .value(ggGroupRole.getRoleArn())
                .description("the Greengrass group role ARN for RR video stream demo")
                .build();

        return ggGroupRole;
    }

    private CfnCoreDefinitionVersion createGreengrassCore(CfnCertificate cert, CfnThing thing) {
        CfnCoreDefinition coreDefinition = CfnCoreDefinition.Builder.create(this, GG_CORE_NAME)
                .name(GG_CORE_NAME)
                .build();

        CfnCoreDefinitionVersion.CoreProperty coreProperty = new CfnCoreDefinitionVersion.CoreProperty.Builder()
                .certificateArn(cert.getAttrArn())
                .id(thing.getRef())
                .thingArn(String.format("arn:aws:iot:%s:%s:thing/%s",
                        this.getRegion(), this.getAccount(), thing.getThingName()))
                .build();

        return CfnCoreDefinitionVersion.Builder.create(this, GG_CORE_VER_NAME)
                .coreDefinitionId(coreDefinition.getRef())
                .cores(Arrays.asList(coreProperty))
                .build();
    }

    @lombok.Data
    private class env {
        private final String ABC = "DEF";
    }

    private CfnFunctionDefinitionVersion.FunctionProperty createGreengrassFunction(@Nullable Version function) {
        CfnFunctionDefinitionVersion.EnvironmentProperty envProp =
                CfnFunctionDefinitionVersion.EnvironmentProperty.builder()
                        .accessSysfs(true)
                        .variables(new env())
                        .build();

        CfnFunctionDefinitionVersion.FunctionConfigurationProperty functionConfigProp =
                CfnFunctionDefinitionVersion.FunctionConfigurationProperty.builder()
                        .pinned(true) // long-lived and keep it running indefinitely
                        .memorySize(64 * 1024) // KB unit
                        .environment(envProp)
                        .timeout(0)
                        .build();

        return CfnFunctionDefinitionVersion.FunctionProperty.builder()
                .id(function.getFunctionName())
                .functionArn(function.getFunctionArn())
                .functionConfiguration(functionConfigProp)
                .build();
    }

    private CfnFunctionDefinitionVersion createGreengrassFunctionVersion(List<Version> functionVersions) {
        CfnFunctionDefinition functionDefinition = CfnFunctionDefinition.Builder.create(this, GG_FUNCTION_NAME)
                .name(GG_FUNCTION_NAME)
                .build();

        ////

        CfnFunctionDefinitionVersion.RunAsProperty runAsProp =
                CfnFunctionDefinitionVersion.RunAsProperty.builder()
                        .gid(0)
                        .uid(0)
                        .build();

        CfnFunctionDefinitionVersion.ExecutionProperty executionProp =
                CfnFunctionDefinitionVersion.ExecutionProperty.builder()
                        .isolationMode("GreengrassContainer")
                        .runAs(runAsProp)
                        .build();

        CfnFunctionDefinitionVersion.DefaultConfigProperty defaultConfigProp =
                CfnFunctionDefinitionVersion.DefaultConfigProperty.builder()
                        .execution(executionProp)
                        .build();

        List<Object> functionProperties = new ArrayList<>(functionVersions.size());

        for (Version function : functionVersions) {
            CfnFunctionDefinitionVersion.FunctionProperty functionProp = this.createGreengrassFunction(function);
            functionProperties.add(functionProp);
        }

        ////

        return CfnFunctionDefinitionVersion.Builder.create(this, GG_FUNCTION_VER_NAME)
                .functionDefinitionId(functionDefinition.getAttrId())
                .defaultConfig(defaultConfigProp)
                .functions(functionProperties)
                .build();
    }

    private void createGreengrassGroup(Role ggGroupRole, CfnCoreDefinitionVersion coreVersion,
                                       CfnFunctionDefinitionVersion functionVersion) {

        CfnGroup group = CfnGroup.Builder.create(this, GG_GROUP_NAME)
                .name(GG_GROUP_NAME)
                .roleArn(ggGroupRole.getRoleArn())
                .build();

        CfnGroupVersion.Builder.create(this, GG_CROUP_VER_NAME)
                .groupId(group.getRef())
                .coreDefinitionVersionArn(coreVersion.getRef())
                .functionDefinitionVersionArn(functionVersion.getRef())
                .build();
    }
}
