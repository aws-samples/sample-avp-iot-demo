
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

## Architecture Overview

This stack deploys:
1. An AWS IoT Thing with certificates and policies
2. An EC2 instance that acts as an IoT device
3. Necessary IAM roles and permissions
4. Integration with an S3 bucket for file storage

The EC2 instance runs a Python script that connects to AWS IoT Core as a device, subscribes to the specified MQTT topic, and processes incoming messages. For security, SSH access to this EC2 instance is restricted to the IP address specified in the `SSHAccessIP` parameter.

## Prerequisites
- AWS CDK CLI installed
- AWS credentials configured
- Node.js and npm installed
- Sufficient AWS permissions to create IoT resources

## Deployment Command
**Note: This stack does not create an S3 bucket, you need to create a bucket before deploying this stack**
```bash
cdk deploy IoTThingStack \
  --parameters SSHAccessIP=10.0.0.100/32 \
  --parameters BucketName=iot-download-bucket \
  --parameters TopicName=my/custom/topic \
  --parameters ThingName=avp-iot-device


## Parameters Explanation

| Parameter | Value | Description |
|-----------|--------|-------------|
| `SSHAccessIP` | `10.0.0.100/32` | Specifies the IP address range allowed to SSH into the EC2 instance that acts as an IoT device. The `/32` suffix indicates a single IP address. For security, this should be your current public IP address. |
| `BucketName` | `iot-download-bucket` | Name of the S3 bucket to be used for IoT file storage. Must be globally unique across all AWS accounts. Used for storing IoT-related files and data. |
| `TopicName` | `my/custom/topic` | MQTT topic name for IoT message routing. Uses forward slashes (`/`) for topic hierarchy. Defines the message path for publishing and subscribing IoT devices. |
| `ThingName` | `avp-iot-device` | Name of the IoT Thing to be created. This will be the identity of your IoT device in AWS IoT Core. |

### Parameter Usage Notes

#### SSHAccessIP
- Must be in CIDR notation (e.g., `203.0.113.1/32`)
- Use `/32` for a single IP address
- Should be set to your current public IP address to allow SSH access to the EC2 IoT device
- Can be updated if your source IP changes
- Critical for security - restricts SSH access to only your IP address

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

#### ThingName
- Unique identifier for your IoT device
- Used to create device certificates and policies
- Will appear in AWS IoT Core console

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

# AVP Stack Deployment Guide

Deploy AVP stack containing API gateway, Lambda functions, Cognito, and AVP reosurces with the following command:

```bash
cdk deploy AvpIotDemoStack
```

## Run value replacer script

When the stack is deployed, execute the value replacer script to automatically replace template values with the output values generated by the CDK stack.

First, cd into the utils directory from root:

```bash
cd utils/
```

Then execute the script:

```bash
python3 value_replacer.py
```

# Running the app locally

Before running the development server, make sure to have the requirement node dependencies installed. To install node dependencies, cd into the web_app directory from root:

```bash
cd web_app/
```

And run the following command:

```bash
npm install
```

Once it’s done running, start the development server with:

```bash
npm run dev
```

The command will open up a server on port 3000. From your browser, navigate to http://localhost:3000/ to view the app. 