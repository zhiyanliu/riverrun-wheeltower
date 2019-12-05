This document means to give you a guide to produce an easy-to-show demonstration about video streaming with object detection and human property recognition result based on Riverrun project.

## 0. Pre-condition

1. Match the requirements listed in README [limit](http://git.awsrun.com/rp/riverrun-wheeltower#limit) section.
2. You need a local laptop/PC as the client to run Riverrun - WheelTower program with your AWS credentials as well as certain rights.
3. AWS IoT Greengress service role should be configured properly. You can follow this [guide](https://docs.aws.amazon.com/greengrass/latest/developerguide/service-role.html) to finish the configuration.

>>**Note:**
>>
>> Riverrun - WheelTower does not require user input any AWS credentials, instead, the default configuration and credentials will be loaded from ``~/.aws/config`` and ``~/.aws/credentials`` automatically, you can configure them by command ``aws configure``.

## 1. Deploy the stack to provision IoT Greengrass and Lambda resources

>>**Note:**
>>
>> All `cdk` and `java` command listed in this guide need you to change current working directory to Riverrun - WheelTower code repository directory first.

- Cleanup last context of CDK

    - ``cdk context --clear``

- Package and upload Lambda function code as the CDK asset

    - ``cdk bootstrap``

- Provision the stack for IoT Greengrass and Lambda resources

    - ``cdk deploy riverrun-video-stream-demo-greengrass``

- Prepare demo asset

    - ``java -jar target/riverrun-wheeltower-1.0-SNAPSHOT-jar-with-dependencies.jar videostream-demo prepare-asset``

## 2. Create fake IoT Greengrass Core device for demo if you have no an own device (optional)

>>**Note:**
>>
>> You need an IoT device to act the "thing" to deploy the Riverrun functions and demo the video streaming with object detection and human property recognition.
>>
>> Skip this step if you have a real one, you can get certificates, credentials and Greengrass Core configuration in the S3 bucket (the bucket name is provided by output `riverrun-video-stream-demo-greengrass.corefilesbucketname` after the stack deployment), then install Greengrass Core and deploy Riverrun functions by yourself.

- ``cdk deploy riverrun-video-stream-demo-dev [-c ec2-key-name=<key-pair-name>] [-c ec2-image-id=<ec2-ami-id>]``
    
    - Update `ec2-image-id` optional parameter in above command to provide AMI ID to provision EC2 instance using an Ubuntu 18.04lts x64 operation system in your region. CDK will lookup an Amazon official AMI contains Ubuntu 18.04lts x64 for your by default.
    - Update `key-pair-name` optional parameter in above command to provide SSH key pair name to inject the public key to the EC2 instance, if you would like to use `ssh` login it, to debug or check log for example.

## 3. Execute Greengrass Group deployment 

- ``java -jar target/riverrun-wheeltower-1.0-SNAPSHOT-jar-with-dependencies.jar videostream-demo deploy-app``

## 4. Send the video streaming and structuring demo data to the Riverrun services

- ``java -jar target/riverrun-wheeltower-1.0-SNAPSHOT-jar-with-dependencies.jar videostream-demo send-data``

    - Login the Greengrass Core device which Riverrun running on, command ``sudo tail -F /opt/greengrass/ggc/var/log/user/*/*/rr-video-stream-demo-VideoStreamer.log`` will print the statistics log about the streaming processing like this:
 
    ```
    the number of received I frame from the source #10 in last 5 seconds: 10
    the number of received slice (include P and B frame) from the source #10 in last 5 seconds: 131
    the number of received SPS from the source #10 in last 5 seconds: 10
    the number of received PPS from the source #10 in last 5 seconds: 10
    count of received synchronized packet from the source #10 in last 5 seconds: 3175
    the number of received RTP packet from the source #10 in last 5 seconds: 3161
    latest received timestamp of synchronized packet: 289
    sent heartbeat to the client (source id #10)
    RTP timestamp reaches 289
    ```

>>**Note:**
>>
>> To represent the video with object bounding box and human property text in the GUI is a TODO item of this Riverrun project for next step.

## -3. Clean demo asset up

- ``java -jar target/riverrun-wheeltower-1.0-SNAPSHOT-jar-with-dependencies.jar videostream-demo cleanup-asset``

## -2. Delete demo IoT Greengrass Core device if you created in step \#2

- ``cdk destroy riverrun-video-stream-demo-dev``

## -1. Destroy the stack to de-provision IoT Greengrass and Lambda resources

- ``cdk destroy riverrun-video-stream-demo-greengrass``

>>**Note:**
>>
>> Currently CDK doesn't support an operation to cleanup bootstrap asset until the [issue](https://github.com/aws/aws-cdk/issues/986) is fixed. You need to manually remove the S3 objects created and the CloudFormation `CDKToolkit` stack.