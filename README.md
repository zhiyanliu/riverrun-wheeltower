## What is this

This is the code repository of the automatic stack deployment and control plane of the demonstration about transformation and synchronization on video streaming and structuring data. The code name of this component is [Riverrun](https://gameofthrones.fandom.com/wiki/Riverrun) - WheelTower, which is the part of Riverrun project and developed by AWS Rapid Prototyping team. 

Mainly, and currently, Riverrun - WheelTower provides three functions:

1. Automatize the IoT and Lambda resources provisioning, as well as the demonstration stack deployment, powered by AWS CDK and CloudFormation service.
2. As a control plane to maximize the automation of the demonstration. Supported demo listed as following:
    - Video streaming with object detection and human property recognition.
3. As the sample code to show the proper way to transmit the video streaming data and structuring data to the Riverrun services by the socket API.

## Why [we](mailto:awscn-sa-prototyping@amazon.com) develop it

As the pair project of [Riverrun](http://git.awsrun.com/rp/riverrun), we would like to automatize the IoT and Lambda resources creation and configuration, more over, to easy the demonstration of Riverrun provided transformation and synchronization functions. We hope this project can assist SA to understand and use our reusable asset quickly and correctly.

>> **Note:**
>>
>> This project is truly under continuative develop stage, we'd like to collect the feedback and include the enhancement in follow-up release to share them with all users. 
>>
>> **DISCLAIMER: This project is NOT intended for a production environment, and USE AT OWN RISK!**  

## Limit

If you would like to try automatic IoT and Lambda resources stack deployment, this project does not work for you if:

* Your device will not manged by AWS IoT Greengrass service.
* You do not have a credential to access WW (non-China) AWS region.
* Your AWS account user has not right to fully access AWS IoT Greengrass, Lambda, CloudFormation or S3 service.
* You do not have a local laptop/PC runs MacOS, Ubuntu or Windows system, to install and run Apache Maven, Java, node, npm and AWS CDK.

Additional, if you would like to try demonstration, it will not work if:

* Your AWS account user has not right to fully access AWS EC2 and VPC services in WW and China AWS regions.

>>**Preferred software version:**
>>
>> - Apache Maven: 3.5.4, or above
>> - Java: 13.0.1 2019-10-15 (build 13.0.1+9), or above
>> - node: v12.12.0, or above but less than 13.2.0 before the [issue](https://github.com/aws/aws-cdk/issues/5187) is fixed.
>> - npm: 6.13.0, or above
>> - CDK: 1.16.1 (build bdbe3aa), or above

## How to build

1. ``git clone git@git.awsrun.com:rp/riverrun-wheeltower.git`` or ``git clone http://git.awsrun.com/rp/riverrun-wheeltower.git``
2. ``cd riverrun-wheeltower``
3. ``mvn package``

## How to play demonstration

- Video streaming with object detection and human property recognition result play guide: [here](http://git.awsrun.com/rp/riverrun-wheeltower/blob/master/demo/video-stream.md)

## Key TODO plan:

- [X] Add `ec2-image-id` parameter for stack `riverrun-video-stream-demo-device-stack` provisioning, when AMI automatically founding not work in user's region.

## Contributor

* Zhi Yan Liu, AWS Rapid Prototyping team,  [liuzhiya@amazon.com](mailto:liuzhiya@amazon.com)
* You. Welcome any feedback and issue report, further more, idea and code contribution are highly encouraged.
