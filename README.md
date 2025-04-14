
# Welcome to your CDK Python project!

This is a blank project for CDK development with Python.

The `cdk.json` file tells the CDK Toolkit how to execute your app.

This project is set up like a standard Python project.  The initialization
process also creates a virtualenv within this project, stored under the `.venv`
directory.  To create the virtualenv it assumes that there is a `python3`
(or `python` for Windows) executable in your path with access to the `venv`
package. If for any reason the automatic creation of the virtualenv fails,
you can create the virtualenv manually.

To manually create a virtualenv on MacOS and Linux:

```
$ python3 -m venv .venv
```

After the init process completes and the virtualenv is created, you can use the following
step to activate your virtualenv.

```
$ source .venv/bin/activate
```

If you are a Windows platform, you would activate the virtualenv like this:

```
% .venv\Scripts\activate.bat
```

Once the virtualenv is activated, you can install the required dependencies.

```
$ pip install -r requirements.txt
```

At this point you can now synthesize the CloudFormation template for this code.

```
$ cdk synth
```

To add additional dependencies, for example other CDK libraries, just add
them to your `setup.py` file and rerun the `pip install -r requirements.txt`
command.

## Useful commands

 * `cdk ls`          list all stacks in the app
 * `cdk synth`       emits the synthesized CloudFormation template
 * `cdk deploy`      deploy this stack to your default AWS account/region
 * `cdk diff`        compare deployed stack with current state
 * `cdk docs`        open CDK documentation

Enjoy!


# IoT Thing Stack Deployment Guide

## Overview
This document describes how to deploy the IoT Thing Stack using AWS CDK (Cloud Development Kit). The stack creates necessary AWS IoT resources with specific configurations for security and messaging.

## Prerequisites
- AWS CDK CLI installed
- AWS credentials configured
- Node.js and npm installed
- Sufficient AWS permissions to create IoT resources

## Deployment Command
```bash
cdk deploy IoTThingStack \
  --parameters SSHAccessIP=10.0.0.100/32 \
  --parameters BucketName=iot-download-bucket \
  --parameters TopicName=my/custom/topic
```

## Parameters Explanation

| Parameter | Value | Description |
|-----------|--------|-------------|
| `SSHAccessIP` | `10.0.0.100/32` | Specifies the IP address range for SSH access. The `/32` suffix indicates a single IP address. Used to restrict SSH connections to a specific source IP for security. |
| `BucketName` | `iot-download-bucket` | Name of the S3 bucket to be created/used for IoT file storage. Must be globally unique across all AWS accounts. Used for storing IoT-related files and data. |
| `TopicName` | `my/custom/topic` | MQTT topic name for IoT message routing. Uses forward slashes (`/`) for topic hierarchy. Defines the message path for publishing and subscribing IoT devices. |

### Parameter Usage Notes

#### SSHAccessIP
- Must be in CIDR notation
- Use `/32` for single IP address
- Can be updated if source IP changes
- Critical for security access control

#### BucketName
- Must be all lowercase
- Can contain hyphens
- Cannot contain underscores
- Must be globally unique
- 3-63 characters in length
- Cannot be formatted as IP address

#### TopicName
- Case sensitive
- Can contain forward slashes
- Used in IoT message routing
- Follows MQTT topic naming conventions
- Supports wildcards in subscriptions


# Running the IoT Subscriber

## Quick Start
```bash
python3 /home/ec2-user/device_code/local_subscribe.py --topic "my/custom/topic"
ls -l /home/ec2-user/device_code/local_subscribe.py
```


## Expected Output
```bash
Initializing IoT subscriber...
Connected to MQTT broker
Subscribing to topic: my/custom/topic
Waiting for messages...
```


## Running in Background
```bash
# Start in background
nohup python3 /home/ec2-user/device_code/local_subscribe.py --topic "my/custom/topic" > subscriber.log 2>&1 &

# Check process
ps aux | grep local_subscribe.py

# View logs
tail -f subscriber.log
```