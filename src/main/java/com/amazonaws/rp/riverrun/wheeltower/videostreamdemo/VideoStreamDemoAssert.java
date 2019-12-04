package com.amazonaws.rp.riverrun.wheeltower.videostreamdemo;

import com.amazonaws.rp.riverrun.wheeltower.utils.Greengrass;
import com.amazonaws.rp.riverrun.wheeltower.utils.S3;
import com.amazonaws.rp.riverrun.wheeltower.utils.StackOutputQuerier;
import com.amazonaws.services.greengrass.AWSGreengrass;
import com.amazonaws.services.greengrass.AWSGreengrassClientBuilder;
import com.amazonaws.services.greengrass.model.*;
import com.amazonaws.services.iot.AWSIot;
import com.amazonaws.services.iot.AWSIotClientBuilder;
import com.amazonaws.services.iot.model.*;
import org.apache.commons.io.FileUtils;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.*;
import java.net.URL;
import java.util.Arrays;
import java.util.List;
import java.util.zip.ZipEntry;
import java.util.zip.ZipOutputStream;

public class VideoStreamDemoAssert {
    private final Logger log = LoggerFactory.getLogger("riverrun-video-stream-demo-asset");
    private final StackOutputQuerier outputQuerier = new StackOutputQuerier();
    private final S3 s3Util = new S3();
    private final Greengrass ggUtils = new Greengrass();

    private final static String PUB_KEY_NAME = "rr-video-stream-demo-greengrass-core-thing-public";
    private final static String PRV_KEY_NAME = "rr-video-stream-demo-greengrass-core-thing-private";
    private final static String ROOT_CA_NAME = "root-ca.crt";

    private final static String CREDENTIALS_FILE_NAME = "credentials.zip";
    private final static String CONFIG_FILE_NAME = "config.json";

    private final String region;

    public VideoStreamDemoAssert(final String region) {
        this.region = region;
    }

    public void provision(final String videoStreamDemoGreengrassStackName) throws IOException {
        String coreFileBucketName = this.outputQuerier.query(
                this.log, videoStreamDemoGreengrassStackName, "corefilesbucketname");
        if (coreFileBucketName == null)
            throw new IllegalArgumentException(String.format(
                    "the name of s3 bucket to save greengrass core assert files not found, " +
                            "is the RR video streamer demo stack %s invalid?", videoStreamDemoGreengrassStackName));

        String certId = this.outputQuerier.query(this.log, videoStreamDemoGreengrassStackName, "certid");
        if (certId == null)
            throw new IllegalArgumentException(String.format("the Greengrass core thing certificate ID not found, " +
                    "is the RR video stream demo stack %s invalid?", videoStreamDemoGreengrassStackName));

        String thingArn = this.outputQuerier.query(this.log, videoStreamDemoGreengrassStackName, "thingarn");
        if (thingArn == null)
            throw new IllegalArgumentException(String.format("the Greengrass core thing ARN not found, " +
                    "is the RR video stream demo stack %s invalid?", videoStreamDemoGreengrassStackName));

        // RiverRun stuff
        String zipFilePath = this.prepareCredentials(certId);
        String configFilePath = this.prepareConfig(thingArn);
        this.s3Util.uploadFile(this.log, coreFileBucketName, zipFilePath);
        this.s3Util.uploadFile(this.log, coreFileBucketName, configFilePath);

        String preSignedCredentialsPackageURL =
                this.s3Util.getObjectPreSignedUrl(coreFileBucketName, VideoStreamDemoAssert.CREDENTIALS_FILE_NAME, 7);
        String preSignedConfigURL =
                this.s3Util.getObjectPreSignedUrl(coreFileBucketName, VideoStreamDemoAssert.CONFIG_FILE_NAME, 7);

        String scriptFilePath = this.prepareSetupScript(preSignedCredentialsPackageURL, preSignedConfigURL);

        this.s3Util.uploadFile(this.log, coreFileBucketName, scriptFilePath);

        log.info(String.format("Greengrass core files is prepared at %s", coreFileBucketName));
    }

    public void deProvision(final String videoStreamDemoGreengrassStackName) {
        String coreFileBucketName = this.outputQuerier.query(
                this.log, videoStreamDemoGreengrassStackName, "corefilesbucketname");
        if (coreFileBucketName == null)
            throw new IllegalArgumentException(String.format(
                    "the name of s3 bucket to save greengrass core assert files not found, " +
                            "is the RR video streamer demo stack %s invalid?", videoStreamDemoGreengrassStackName));

        String greengrassGroupId = this.outputQuerier.query(
                this.log, videoStreamDemoGreengrassStackName, "greengrassgroupid");
        if (greengrassGroupId == null)
            throw new IllegalArgumentException(String.format("the Greengrass group ID not found, " +
                    "is the RR video stream demo stack %s invalid?", videoStreamDemoGreengrassStackName));

        String certId = this.outputQuerier.query(this.log, videoStreamDemoGreengrassStackName, "certid");
        if (certId == null)
            throw new IllegalArgumentException(String.format("the Greengrass core thing certificate ID not found, " +
                    "is the RR video stream demo stack %s invalid?", videoStreamDemoGreengrassStackName));

        this.deactivateThingCert(certId);
        log.info(String.format("Greengrass core thing certificate %s is deactivated", certId));

        this.s3Util.emptyBucket(this.log, coreFileBucketName);
        log.info(String.format("Greengrass core files S3 bucket %s is cleaned up to empty", coreFileBucketName));

        this.ggUtils.resetGroupDeployment(this.log, greengrassGroupId);
        log.info(String.format("Greengrass group %s deployment is reset", greengrassGroupId));
    }

    public void deployApp(final String videoStreamDemoGreengrassStackName) {
        String greengrassGroupId = this.outputQuerier.query(
                this.log, videoStreamDemoGreengrassStackName, "greengrassgroupid");
        if (greengrassGroupId == null)
            throw new IllegalArgumentException(String.format("the Greengrass group ID not found, " +
                    "is the RR video stream demo stack %s invalid?", videoStreamDemoGreengrassStackName));

        String deploymentId = this.createGreengressDeployment(greengrassGroupId);

        this.ggUtils.waitGroupDeployDone(this.log, greengrassGroupId, deploymentId);

        log.info("Riverrun has been deployed on the device by Greengrass core");
    }

    private String createGreengressDeployment(final String greengrassGroupId) {
        AWSGreengrass greengrassClient = AWSGreengrassClientBuilder.defaultClient();

        log.debug("connected to AWS Greengrass service");

        ListGroupVersionsRequest listGroupVersionsRequest = new ListGroupVersionsRequest();
        listGroupVersionsRequest.setGroupId(greengrassGroupId);
        listGroupVersionsRequest.setMaxResults("10");

        ListGroupVersionsResult listGroupVersionsResult = greengrassClient.listGroupVersions(listGroupVersionsRequest);
        if (listGroupVersionsResult.getVersions().size() != 1)
            throw new IllegalArgumentException(String.format("the Greengrass group id %s is invalid, " +
                    "is it created by RR video stream demo stack?", greengrassGroupId));

        CreateDeploymentRequest deploymentReq = new CreateDeploymentRequest();
        deploymentReq.setDeploymentType(DeploymentType.NewDeployment);
        deploymentReq.setGroupId(greengrassGroupId);
        deploymentReq.setGroupVersionId(listGroupVersionsResult.getVersions().get(0).getVersion());

        CreateDeploymentResult result = greengrassClient.createDeployment(deploymentReq);

        return result.getDeploymentId();
    }

    private void generateCredentials(final String certId, final String certFilePath, final String rootCaPath,
                                     String publicKeyPath, String privateKeyPath) throws IOException {

        AWSIot iotClient = AWSIotClientBuilder.defaultClient();

        log.debug("connected to AWS IoT service");

        log.debug(String.format("fetching certificate %s ...", certId));

        DescribeCertificateRequest req = new DescribeCertificateRequest();
        req.setCertificateId(certId);
        DescribeCertificateResult describeCertificateResult = iotClient.describeCertificate(req);
        CertificateDescription certDesc = describeCertificateResult.getCertificateDescription();

        PrintWriter out = new PrintWriter(certFilePath);
        out.print(certDesc.getCertificatePem());
        out.close();

        log.info(String.format("the IoT device certificate %s is downloaded at %s, status: %s",
                certId, certFilePath, certDesc.getStatus()));

        String fileName = String.format("rr-video-stream-demo/%s", ROOT_CA_NAME);
        URL rootCa = getClass().getClassLoader().getResource(fileName);
        if (rootCa == null)
            throw new IllegalArgumentException(
                    String.format("root CA certificate file %s not found", fileName));

        out = new PrintWriter(rootCaPath);
        out.print(new String(rootCa.openStream().readAllBytes()));
        out.close();

        log.info(String.format("the IoT device root CA certificate is generated at %s", rootCaPath));

        fileName = String.format("rr-video-stream-demo/%s.key", PUB_KEY_NAME);
        URL key = getClass().getClassLoader().getResource(fileName);
        if (key == null)
            throw new IllegalArgumentException(String.format("private key file %s not found", fileName));

        out = new PrintWriter(publicKeyPath);
        out.print(new String(key.openStream().readAllBytes()));
        out.close();

        log.info(String.format("the IoT device public key is generated at %s", publicKeyPath));

        fileName = String.format("rr-video-stream-demo/%s.key", PRV_KEY_NAME);
        key = getClass().getClassLoader().getResource(fileName);
        if (key == null)
            throw new IllegalArgumentException(String.format("private key file %s not found", fileName));

        out = new PrintWriter(privateKeyPath);
        out.print(new String(key.openStream().readAllBytes()));
        out.close();

        log.info(String.format("the IoT device private key is generated at %s", privateKeyPath));
    }

    private String prepareCredentials(final String certId) throws IOException {
        String credentialsPath = String.format("%s/target/video-stream-demo/credentials",
                System.getProperty("user.dir"));

        File credentialsPathFile = new File(credentialsPath);
        FileUtils.deleteDirectory(credentialsPathFile);
        boolean ok = credentialsPathFile.mkdirs();
        if (!ok)
            throw new IOException(
                    String.format("failed to create IoT device credentials directory at %s", credentialsPath));

        String certFilePath = String.format("%s/cert.pem", credentialsPath);
        String rootCaPath = String.format("%s/root-ca.crt", credentialsPath);
        String publicKeyPath = String.format("%s/public.key", credentialsPath);
        String privateKeyPath = String.format("%s/private.key", credentialsPath);

        this.generateCredentials(certId, certFilePath, rootCaPath, publicKeyPath, privateKeyPath);

        List<String> srcFiles = Arrays.asList(certFilePath, rootCaPath, publicKeyPath, privateKeyPath);
        String zipFilePath = String.format("%s/%s", credentialsPath, CREDENTIALS_FILE_NAME);
        FileOutputStream fos = new FileOutputStream(zipFilePath);
        ZipOutputStream zipOut = new ZipOutputStream(fos);

        for (String srcFile : srcFiles) {
            File fileToZip = new File(srcFile);
            FileInputStream fis = new FileInputStream(fileToZip);
            ZipEntry zipEntry = new ZipEntry(fileToZip.getName());
            zipOut.putNextEntry(zipEntry);

            byte[] bytes = new byte[1024];
            int length;
            while ((length = fis.read(bytes)) >= 0) {
                zipOut.write(bytes, 0, length);
            }
            fis.close();
        }

        zipOut.close();
        fos.close();

        log.info(String.format("the credentials package of the Greengrass core are prepared at %s", zipFilePath));

        return zipFilePath;
    }

    public String prepareConfig(final String thingArn) throws IOException {
        DescribeEndpointRequest req = new DescribeEndpointRequest();
        // for China region (not support yet, mentioned in README), use iot:Data instead
        req.setEndpointType("iot:Data-ATS");

        AWSIot client = AWSIotClientBuilder.defaultClient();
        DescribeEndpointResult result = client.describeEndpoint(req);
        String iotServiceEndpoint = result.getEndpointAddress();

        String ggServiceEndpoint = String.format("greengrass-ats.iot.%s.amazonaws.com", this.region);

        String configDstPath = String.format("%s/target/video-stream-demo/config",
                System.getProperty("user.dir"));

        File configDstPathFile = new File(configDstPath);
        FileUtils.deleteDirectory(configDstPathFile);
        boolean ok = configDstPathFile.mkdirs();
        if (!ok)
            throw new IOException(String.format(
                    "failed to create Greengrass core config directory at %s", configDstPath));

        String configDstFilePath = String.format("%s/%s", configDstPath, CONFIG_FILE_NAME);

        String configSrcFileName = String.format("rr-video-stream-demo/%s", CONFIG_FILE_NAME);
        URL configSrc = getClass().getClassLoader().getResource(configSrcFileName);
        if (configSrc == null)
            throw new IllegalArgumentException(
                    String.format("config file %s not found", configSrcFileName));

        String config = new String(configSrc.openStream().readAllBytes());

        config = config.replace("<CORE_THING_ARN>", thingArn);
        config = config.replace("<IOT_SERVICE_ENDPOINT>", iotServiceEndpoint);
        config = config.replace("<GREENGRASS_SERVICE_ENDPOINT>", ggServiceEndpoint);

        PrintWriter out = new PrintWriter(configDstFilePath);
        out.print(config);
        out.close();

        log.info(String.format("config of the Greengrass core are prepared at %s", configDstFilePath));

        return configDstFilePath;
    }

    private String prepareSetupScript(String preSignedCredentialsPackageURL,
                                      String preSignedConfigURL) throws IOException {
        String scriptDstPath = String.format("%s/target/video-stream-demo/setup-script",
                System.getProperty("user.dir"));

        File scriptDstPathFile = new File(scriptDstPath);
        FileUtils.deleteDirectory(scriptDstPathFile);
        boolean ok = scriptDstPathFile.mkdirs();
        if (!ok)
            throw new IOException(String.format(
                    "failed to create Greengrass core setup script directory at %s", scriptDstPath));

        String scriptDstFilePath = String.format(
                "%s/%s", scriptDstPath, VideoStreamDemoDeviceStack.SETUP_SCRIPT_FILE_NAME);

        String scriptSrcFileName = String.format(
                "rr-video-stream-demo/%s", VideoStreamDemoDeviceStack.SETUP_SCRIPT_FILE_NAME);
        URL scriptSrc = getClass().getClassLoader().getResource(scriptSrcFileName);
        if (scriptSrc == null)
            throw new IllegalArgumentException(
                    String.format("setup script file %s not found", scriptSrcFileName));

        String script = new String(scriptSrc.openStream().readAllBytes());

        script = script.replace("<CREDENTIALS_PACKAGE_URL>", preSignedCredentialsPackageURL);
        script = script.replace("<GREENGRASS_CORE_CONFIG_URL>", preSignedConfigURL);

        PrintWriter out = new PrintWriter(scriptDstFilePath);
        out.print(script);
        out.close();

        log.info(String.format("setup script of the IoT device are prepared at %s", scriptDstFilePath));

        return scriptDstFilePath;
    }

    private void deactivateThingCert(String certId) {
        AWSIot iotClient = AWSIotClientBuilder.defaultClient();
        log.debug("connected to AWS IoT service");

        try {
            // Deactivate three certificates
            //      CLI: aws iot update-certificate --new-status INACTIVE --certificate-id <certificate-id>
            UpdateCertificateRequest req = new UpdateCertificateRequest();
            req.setCertificateId(certId);
            req.setNewStatus("INACTIVE");
            iotClient.updateCertificate(req);
        } catch (Exception e) {
            if (!e.getMessage().contains("does not exist"))
                throw e;
        }

        log.info(String.format("the certificate %s is deactivated", certId));
    }
}
