
# Implement role-based access control (RBAC) to IoT devices with Amazon Verified Permissions

This is a sample cdk project used to demo [Amazon Verified Permissions](https://aws.amazon.com/verified-permissions/) integration with [AWS IoT](https://aws.amazon.com/iot-core/).  [Click here to view the blog{WIP}](www.example.com)

This project is set up like a standard [CDK Python project](https://docs.aws.amazon.com/cdk/v2/guide/work-with-cdk-python.html).  The initialization
process also creates a virtualenv within this project, stored under the `.venv`
directory.  To create the virtualenv it assumes that there is a `python3`
(or `python` for Windows) executable in your path with access to the `venv`
package. If for any reason the automatic creation of the virtualenv fails,
you can create the virtualenv manually.

To manually create a virtualenv on MacOS and Linux:

```bash
python3 -m venv .venv
```

After the init process completes and the virtualenv is created, you can use the following
step to activate your virtualenv.

```bash
source .venv/bin/activate
```

If you are a Windows platform, you would activate the virtualenv like this:

```bash
% .venv\Scripts\activate.bat
```

Once the virtualenv is activated, you can install the required dependencies.

```bash
pip install -r requirements.txt
```

At this point you can now synthesize the CloudFormation template for this code.

``` bash
cdk synth -e <StackName>
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

# IoT Thing Stack Deployment Guide

## Architecture Overview

This stack deploys:

1. An AWS IoT Thing with certificates and policies
2. An EC2 instance that acts as an IoT device
3. Necessary IAM roles and permissions
4. Integration with an S3 bucket for file storage

The EC2 instance runs a Python script that connects to AWS IoT Core as a device, subscribes to the specified MQTT topic, and processes incoming messages.

## Prerequisites

* AWS CDK CLI installed

* AWS credentials configured

* Node.js and npm installed

* Sufficient AWS permissions to create resources in the IoT Stack

## Deployment Command

Before deploying the stack for the first time, you will need to bootstrap your environment with the following command:

```bash
cdk bootstrap
```

**Note: This stack does not create an S3 bucket, you need to create a bucket before deploying this stack**

```bash
cdk deploy IoTThingStack \
  --parameters BucketName=iot-download-bucket \
  --parameters TopicName=my/custom/topic \
  --parameters ThingName=avp-iot-device
```



## Parameters Explanation

| Parameter | Value | Description |
|-----------|--------|-------------|
| `BucketName` | `iot-download-bucket` | Name of the S3 bucket to be used for IoT file storage. This bucket should be created before deploying the stack. Also the bucket has to exist in the same AWS region as the Stack |
| `TopicName` | `my/custom/topic` | MQTT topic name for IoT message routing. Uses forward slashes (`/`) for topic hierarchy. Defines the message path for publishing and subscribing IoT devices. For the purposes of this blog this will be the topic that the IoT device will subscribe to download files from S3|
| `ThingName` | `avp-iot-device` | Name of the IoT Thing to be created. This will be the identity of your IoT device in AWS IoT Core. For the purposes of this blog, this will be the device that can be listed or the remote commands that will be sent to based on the persona logged into the WebApp|

# Running the IoT Subscriber

## Login to the EC2 device

As part of this demo an EC2 instance will be deployed that acts as an IoT Thing. You can use the EC2 session manager to login to the device.

## Start the IoT code that downloads the file from S3

Switch to root user (superuser) by running the following command:

```bash
sudo su
```

Run the Python script:

```bash
python3 /home/ec2-user/device_code/local_subscribe.py --topic my/custom/topic --client-id avp-iot-device
```

**Note**: 

* Replace `my/custom/topic` and `avp-iot-device` with names used for IoT topic name and IoT Thing name while deploying `IoTThingStack`

* if the script returns an error for disconnect or connects to us-east-1 endpoint while stack is deployed in another region  make sure you set export AWS_DEFAULT_REGION="Stack region name For example us-west-2"

## Expected Output

```bash
Initializing IoT subscriber...
Connected to MQTT broker
Subscribing to topic: my/custom/topic
Subscribed to topic: my/custom/topic
```

## Running in the background

**Note: Replace `my/custom/topic` and `avp-iot-device` with names used for IoT topic name and IoT Thing name while deploying `IoTThingStack`**

```bash
# Start in background
nohup python3 /home/ec2-user/device_code/local_subscribe.py --topic my/custom/topic --client-id avp-iot-device > subscriber.log 2>&1 &

# Check process
ps aux | grep local_subscribe.py

# View logs
tail -f subscriber.log
```

# AVP Stack Deployment Guide

Deploy AVP stack containing API gateway, Lambda functions, Cognito, and AVP reosurces with the following command:

```bash
cdk deploy AvpIotDemoStack --outputs-file outputs.json
```

## Run value replacer script

When the stack is deployed, execute the value replacer script to automatically replace template values with the output values generated by the CDK stack.

First, cd into the utils directory from root:

```bash
cd utils/
```

Then execute the script:

```bash
python3 values_replacer.py
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

The command will open up a server on port 3000. From your browser, navigate to <http://localhost:3000/> to view the app.

# Setup the user permission on AWS Console

## Create an Amazon Cognito User

1. Navigate to the Amazon Cognito console
2. Locate and click on the user pool created via AWS CDK
3. From the left side panel, select "Users"
4. On the top right, click on the "Create User" button
   1. Select the "Don't send an invitation" option for Invitation message
   2. Type your email address for the Email Address field
   3. Set a password for the user
   4. Click on "Create User" when finished

**Note:** You will be prompted to change your password upon first login into the application

## Add Amazon Cognito User to Group

1. Navigate to the Amazon Cognito console
2. Locate and click on the user pool created via AWS CDK
3. From the left side panel, select "Groups"
4. Click on the manager group
5. On the right, click on the "Add user to group" button
6. Select the previously created user, and click on "Add"

## Important Notes

* The user has now been added to the manager group. You can repeat the same process for the operator group, but ensure a user is only part of one group, either manager or operator.
* The group information for a user is contained in the JWT token issued on each login. A sign out is required to reset the group tied to a user.
* Amazon Cognito user pools help you manage user directories and handle user authentication and authorization.
