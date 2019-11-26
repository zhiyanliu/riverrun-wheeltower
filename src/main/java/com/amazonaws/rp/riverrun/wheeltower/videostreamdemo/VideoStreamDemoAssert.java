package com.amazonaws.rp.riverrun.wheeltower.videostreamdemo;

import com.amazonaws.SdkClientException;
import com.amazonaws.rp.riverrun.wheeltower.utils.StackOutputQuerier;
import com.amazonaws.services.s3.AmazonS3;
import com.amazonaws.services.s3.AmazonS3ClientBuilder;
import com.amazonaws.services.s3.model.ObjectMetadata;
import com.amazonaws.services.s3.model.PutObjectRequest;
import org.apache.commons.io.FileUtils;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.net.URL;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

public class VideoStreamDemoAssert {
    private final Logger log = LoggerFactory.getLogger("riverrun-video-stream-demo-asset");
    private final StackOutputQuerier outputQuerier = new StackOutputQuerier();

    private final static String METADATA_FRAME_EMITTER_FUNC_FILE_NAME = "MetadataFrameEmitterFunction.zip";
    private final static String VIDEO_EMITTER_FUNC_FILE_NAME = "VideoEmitterFunction.zip";
    private final static String VIDEO_PROCESSOR_FUNC_FILE_NAME = "VideoProcessorFunction.zip";
    private final static String VIDEO_STREAMER_FUNC_FILE_NAME = "VideoStreamerFunction.zip";

    private final static String PUB_KEY_NAME = "rr-video-stream-demo-greengrass-core-thing-public";
    private final static String PRV_KEY_NAME = "rr-video-stream-demo-greengrass-core-thing-private";
    private final static String ROOT_CA_NAME = "root-ca.crt";

    private final static String CREDENTIALS_FILE_NAME = "credentials.zip";
    private final static String GG_CORE_CONFIG_FILE_NAME = "rr-video-stream-demo-greengrass-core-config.json";
    private final static String SETUP_SCRIPT_FILE_NAME = "setup.py";

    public void provisionLambda(final String videoStreamDemoIoTStackName) throws IOException {
        String coreFileBucketName = this.queryCoreFileBucketName(videoStreamDemoIoTStackName);
        if (coreFileBucketName == null)
            throw new IllegalArgumentException(String.format(
                    "the name of s3 bucket to save greengrass core assert files not found, " +
                            "is the RR video streamer demo stack %s invalid?", videoStreamDemoIoTStackName));

        List<String> functionZipFilePaths = this.prepareFunctions();
        this.uploadRiverrunFunctions(coreFileBucketName, functionZipFilePaths);
    }

    public void provisionAsset(final String videoStreamDemoGreengrassStackName) throws IOException {

    }

    public void deProvision(final String videoStreamDemoGreengrassStackName) throws IOException {

    }

    private String queryCoreFileBucketName(String videoStreamDemoIoTStackName) {
        return this.outputQuerier.query(videoStreamDemoIoTStackName, "corefilesbucketname");
    }

    private List<String> prepareFunctions() throws IOException {
        String functionsPath = String.format("%s/target/rr-video-stream-demo/functions",
                System.getProperty("user.dir"));

        File functionsPathFile = new File(functionsPath);
        FileUtils.deleteDirectory(functionsPathFile);
        boolean ok = functionsPathFile.mkdirs();
        if (!ok)
            throw new IOException(
                    String.format("failed to create lambda functions directory at %s", functionsPath));

        List<String> functionNames = Arrays.asList("metadata frame emitter", "video emitter",
                "video processor", "video streamer");
        List<String> functionZipFileNames = Arrays.asList(
                METADATA_FRAME_EMITTER_FUNC_FILE_NAME, VIDEO_EMITTER_FUNC_FILE_NAME,
                VIDEO_PROCESSOR_FUNC_FILE_NAME, VIDEO_STREAMER_FUNC_FILE_NAME);
        List<String> functionZipFilePaths = new ArrayList<>(4);

        for (String functionZipFileName : functionZipFileNames)
            functionZipFilePaths.add(String.format("%s/%s", functionsPath, functionZipFileName));

        for (int i = 0; i < functionZipFilePaths.size(); i++) {
            String fileName = String.format("riverrun-noarch/%s", functionZipFileNames.get(i));
            URL zip = getClass().getClassLoader().getResource(fileName);
            if (zip == null)
                throw new IllegalArgumentException(String.format(
                        "the lambda function %s zip file %s not found", functionNames.get(i), fileName));

            FileOutputStream out = new FileOutputStream(functionZipFilePaths.get(i));
            out.write(zip.openStream().readAllBytes());
            out.close();

            log.info(String.format(
                    "the lambda function %s is generated at %s", functionNames.get(i), functionZipFilePaths.get(i)));
        }

        log.info(String.format("lambda functions of the greengrass core are prepared at %s", functionsPath));

        return functionZipFilePaths;
    }

    private void uploadRiverrunFunctions(final String coreFileBucketName,
                                         final List<String> functionZipFilePaths) throws IOException {
        try {
            AmazonS3 s3Client = AmazonS3ClientBuilder.standard().build();

            log.debug("connected to AWS S3 service");

            for (String functionZipFilePath : functionZipFilePaths) {
                File file = new File(functionZipFilePath);
                PutObjectRequest req = new PutObjectRequest(coreFileBucketName, file.getName(), file);
                ObjectMetadata metadata = new ObjectMetadata();
                metadata.setContentType("application/octet-stream");

                log.debug(String.format("uploading Riverrun function %s ...", file.getName()));

                s3Client.putObject(req);

                log.info(String.format("Riverrun function file %s uploaded to the bucket %s",
                        file.getName(), coreFileBucketName));
            }
        } catch (SdkClientException e) {
            e.printStackTrace();
            log.error(String.format("failed to upload Riverrun function file to S3 bucket %s", coreFileBucketName));
            throw e;
        }

        log.info("all Riverrun function files are prepared");
    }
}
