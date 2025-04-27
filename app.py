#!/usr/bin/env python3
import os

import aws_cdk as cdk
from cdk_nag import AwsSolutionsChecks, NagSuppressions, NagPackSuppression

from avp_iot_demo.avp_iot_demo_stack import AvpIotDemoStack
from iot_stack.ec2_iot_device import IoTThingStack

app = cdk.App()
iot_stack = IoTThingStack(app, "IoTThingStack")
AvpIotDemoStack(app, "AvpIotDemoStack", config_path="web_app/amplify_outputs.json")
# Add CDK Nag to all stacks in the app
cdk.Aspects.of(app).add(AwsSolutionsChecks())

# Add global suppressions for common issues
NagSuppressions.add_stack_suppressions(
    iot_stack,
    [
        # Suppress IAM4 for all Lambda roles using managed policies
        {
            "id": "AwsSolutions-IAM4",
            "reason": "Using managed policies for Lambda execution roles in demo environment",
            "appliesTo": [
                "Policy::arn:<AWS::Partition>:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
            ]
        },
        # Suppress L1 for Lambda runtimes
        {
            "id": "AwsSolutions-L1",
            "reason": "Using stable Python runtime for Lambda functions"
        },
        # Suppress VPC7 for VPC Flow Logs
        {
            "id": "AwsSolutions-VPC7",
            "reason": "VPC Flow Logs not required for demo environment"
        },
        # Suppress EC26, EC28, EC29 for EC2 instances
        {
            "id": "AwsSolutions-EC26",
            "reason": "EBS encryption not required for demo environment"
        },
        {
            "id": "AwsSolutions-EC28",
            "reason": "Detailed monitoring not required for demo environment"
        },
        {
            "id": "AwsSolutions-EC29",
            "reason": "Termination protection not required for demo environment"
        }
    ]
)

# Add specific suppressions for the IAM5 findings
NagSuppressions.add_resource_suppressions_by_path(
    iot_stack,
    "/IoTThingStack/CreateCertLambdaRole/Resource",
    [
        {
            "id": "AwsSolutions-IAM5",
            "reason": "CloudWatch Logs permissions require wildcard for Lambda to create log groups and streams",
            "appliesTo": [
                "Resource::arn:aws:logs:<AWS::Region>:<AWS::AccountId>:log-group:/aws/lambda/*"
            ]
        }
    ]
)

NagSuppressions.add_resource_suppressions_by_path(
    iot_stack,
    "/IoTThingStack/CreateCertLambdaRole/DefaultPolicy/Resource",
    [
        {
            "id": "AwsSolutions-IAM5",
            "reason": "SSM parameter path uses wildcard to allow access to all parameters under the IoT thing path",
            "appliesTo": [
                "Resource::arn:aws:ssm:<AWS::Region>:<AWS::AccountId>:parameter/iot/<ThingName>/*"
            ]
        },
        {
            "id": "AwsSolutions-IAM5",
            "reason": "Certificate ARN is not known until runtime, so wildcard is required",
            "appliesTo": [
                "Resource::arn:aws:iot:<AWS::Region>:<AWS::AccountId>:cert/*"
            ]
        },
        {
            "id": "AwsSolutions-IAM5",
            "reason": "IoT list operations require wildcard permissions as they operate across multiple resource types",
            "appliesTo": [
                "Resource::arn:aws:iot:<AWS::Region>:<AWS::AccountId>:*"
            ]
        }
    ]
)

NagSuppressions.add_resource_suppressions_by_path(
    iot_stack,
    "/IoTThingStack/CertProvider/framework-onEvent/ServiceRole/DefaultPolicy/Resource",
    [
        {
            "id": "AwsSolutions-IAM5",
            "reason": "Lambda function ARN wildcard is required for custom resource provider",
            "appliesTo": [
                "Resource::<CreateCertLambda0309D0BB.Arn>:*"
            ]
        }
    ]
)

NagSuppressions.add_resource_suppressions_by_path(
    iot_stack,
    "/IoTThingStack/EC2Role/DefaultPolicy/Resource",
    [
        {
            "id": "AwsSolutions-IAM5",
            "reason": "SSM parameter path uses wildcard to allow access to all parameters under the IoT thing path",
            "appliesTo": [
                "Resource::arn:aws:ssm:<AWS::Region>:<AWS::AccountId>:parameter/iot/<ThingName>/*"
            ]
        },
        {
            "id": "AwsSolutions-IAM5",
            "reason": "S3 bucket access requires wildcard for object operations",
            "appliesTo": [
                "Resource::arn:aws:s3:::<BucketName>/*",
                "Resource::arn:<AWS::Partition>:s3:::*-assets-<AWS::AccountId>-<AWS::Region>/*"
            ]
        },
        {
            "id": "AwsSolutions-IAM5",
            "reason": "S3 actions require wildcards for common operations",
            "appliesTo": [
                "Action::s3:GetBucket*",
                "Action::s3:GetObject*",
                "Action::s3:List*"
            ]
        }
    ]
)

# Add a general suppression for any remaining IAM5 findings
NagSuppressions.add_stack_suppressions(
    iot_stack,
    [
        {
            "id": "AwsSolutions-IAM5",
            "reason": "Using wildcards for demo environment and APIs that require wildcards"
        }
    ]
)




app.synth()
