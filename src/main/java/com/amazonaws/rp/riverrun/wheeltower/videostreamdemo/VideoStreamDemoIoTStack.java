package com.amazonaws.rp.riverrun.wheeltower.videostreamdemo;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.SerializationFeature;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import software.amazon.awscdk.core.*;
import software.amazon.awscdk.services.iot.*;
import software.amazon.awscdk.services.s3.BlockPublicAccess;
import software.amazon.awscdk.services.s3.BlockPublicAccessOptions;
import software.amazon.awscdk.services.s3.Bucket;
import software.amazon.awscdk.services.s3.BucketProps;

import java.io.IOException;
import java.net.URL;
import java.util.Objects;
import java.util.Random;

public class VideoStreamDemoIoTStack extends Stack {
    private final Logger log = LoggerFactory.getLogger("riverrun-video-stream-demo-iot-stack");

    private final static ObjectMapper JSON =
            new ObjectMapper().configure(SerializationFeature.INDENT_OUTPUT, true);

    private final static String POLICY_NAME = "rr-video-stream-demo-greengrass-core-thing-policy";
    private final static String THING_NAME = "rr-video-stream-demo-greengrass-core-thing";
    private final static String CSR_NAME = "rr-video-stream-demo-greengrass-core-thing-csr";
    private final static String CERT_NAME = "rr-video-stream-demo-greengrass-core-thing-cert";

    private final static String CORE_FILE_BUCKET_NAME = "rr-video-stream-demo-core-files";

    private final String coreFileBucketName;

    public VideoStreamDemoIoTStack(final Construct parent, final String id) throws IOException {
        this(parent, id, null);
    }

    public VideoStreamDemoIoTStack(final Construct parent, final String id,
                                   final StackProps props) throws IOException {
        super(parent, id, props);

        Random rand = new Random();
        this.coreFileBucketName = String.format("%s-%d", CORE_FILE_BUCKET_NAME, Math.abs(rand.nextLong()));

        // IoT thing stuff
        CfnPolicy policy = this.createThingPolicy();
        CfnThing thing = this.createThing();
        this.createThingCert(policy, thing);
        this.createCoreFileS3Bucket();
    }

    private CfnPolicy createThingPolicy() throws IOException {
        // Create a policy
        String fileName = String.format("rr-video-stream-demo/%s.json", POLICY_NAME);
        URL inlinePolicyDoc = getClass().getClassLoader().getResource(fileName);
        if (inlinePolicyDoc == null)
            throw new IllegalArgumentException(String.format("the policy statement file %s not found", fileName));
        JsonNode node = JSON.readTree(inlinePolicyDoc);

        CfnPolicy policy = new CfnPolicy(this, POLICY_NAME, CfnPolicyProps.builder()
                .withPolicyName(POLICY_NAME)
                .withPolicyDocument(node)
                .build());

        // Output the policy configuration
        new CfnOutput(this, "policy-name", CfnOutputProps.builder()
                .withValue(Objects.requireNonNull(policy.getPolicyName()))
                .withDescription("the policy name for RR video stream demo")
                .build());

        new CfnOutput(this, "policy-arn", CfnOutputProps.builder()
                .withValue(policy.getAttrArn())
                .withDescription("the policy arn for RR video stream demo")
                .build());

        return policy;
    }

    private CfnThing createThing() {
        // Create a thing
        CfnThing thing = new CfnThing(this, THING_NAME, CfnThingProps.builder()
                .withThingName(THING_NAME)
                .build());

        // Output the thing configuration
        new CfnOutput(this, "thing-name", CfnOutputProps.builder()
                .withValue(Objects.requireNonNull(thing.getThingName()))
                .withDescription("the thing name for RR video stream demo")
                .build());

        new CfnOutput(this, "thing-arn", CfnOutputProps.builder()
                .withValue(String.format("arn:aws:iot:%s:%s:thing/%s",
                        this.getRegion(), this.getAccount(), thing.getThingName()))
                .withDescription("the thing ARN for RR video stream demo")
                .build());

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
        CfnCertificate cert = new CfnCertificate(this, CERT_NAME, CfnCertificateProps.builder()
                .withCertificateSigningRequest(csrPem)
                .withStatus("ACTIVE")
                .build());

        cert.addDependsOn(policy);
        cert.addDependsOn(thing);

        // Attach the policy to the certificate
        new CfnPolicyPrincipalAttachment(this, "rr-video-stream-demo-policy2cert",
                CfnPolicyPrincipalAttachmentProps.builder()
                        .withPolicyName(POLICY_NAME)
                        .withPrincipal(cert.getAttrArn())
                        .build());

        // Attach the certificate to the thing
        new CfnThingPrincipalAttachment(this, "rr-video-stream-demo-cert2thing",
                CfnThingPrincipalAttachmentProps.builder()
                        .withThingName(THING_NAME)
                        .withPrincipal(cert.getAttrArn())
                        .build());

        // Output the thing configuration
        new CfnOutput(this, "cert-id", CfnOutputProps.builder()
                .withValue(cert.getRef())
                .withDescription("the thing certificate ID for RR video stream demo")
                .build());

        new CfnOutput(this, "cert-arn", CfnOutputProps.builder()
                .withValue(cert.getAttrArn())
                .withDescription("the thing certificate ARN for RR video stream demo")
                .build());

        return cert;
    }

    private void createCoreFileS3Bucket() {
        Bucket coreFileBucket = new Bucket(this, this.coreFileBucketName, BucketProps.builder()
                .withBlockPublicAccess(new BlockPublicAccess(BlockPublicAccessOptions.builder()
                        .withBlockPublicAcls(false)
                        .withBlockPublicPolicy(true)
                        .withRestrictPublicBuckets(true)
                        .build()))
                .withRemovalPolicy(RemovalPolicy.DESTROY)
                .withPublicReadAccess(false)
                .withBucketName(this.coreFileBucketName)
                .build());

        new CfnOutput(this, "core-files-bucket-name", CfnOutputProps.builder()
                .withValue(coreFileBucket.getBucketName())
                .withDescription("the name of s3 bucket to save greengrass core assert files " +
                        "to act IoT device for RR video stream demo")
                .build());
    }
}
