# your_project/iot_thing_stack.py

from aws_cdk import (
    Stack,
    aws_iot as iot,
    aws_lambda as lambda_,
    aws_iam as iam,
    aws_ssm as ssm,
    aws_ec2 as ec2,
    CfnOutput,
    CustomResource,
    custom_resources as cr,
    CfnParameter,
    aws_s3_assets as assets,
    Duration,
    Aspects,
    RemovalPolicy
)
from cdk_nag import NagSuppressions, NagPackSuppression

from constructs import Construct
import os

class IoTThingStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)


        # Create an asset from the device_code folder
        device_code = assets.Asset(
            self, "DeviceCode",
            path="iot_stack/device_code"
        )

        


        bucket_parameter = CfnParameter(
            self, "BucketName",
            type="String",
            description="Name of the S3 bucket to access",
            constraint_description="Must be a valid S3 bucket name"
        )

        # Define topic parameter
        topic_parameter = CfnParameter(
            self, "TopicName",
            type="String",
            description="IoT Core topic to subscribe to",
            default="my/topic/name"
        )

        # Define thing name as a parameter
        thing_name_parameter = CfnParameter(
            self, "ThingName",
            type="String",
            description="Name of the IoT Thing",
            default="avp-iot-device"
        )

        # Use the parameter throughout the code
        thing_name = thing_name_parameter.value_as_string


        # # Define the IoT Policy with more specific resources
        # iot_policy = iot.CfnPolicy(
        #     self, "IoTPolicy",
        #     policy_name=f"{thing_name}-policy",
        #     policy_document={
        #         "Version": "2012-10-17",
        #         "Statement": [
        #             {
        #                 "Effect": "Allow",
        #                 "Action": [
        #                     "iot:Connect"
        #                 ],
        #                 "Resource": [f"arn:aws:iot:{self.region}:{self.account}:client/{thing_name}"]
        #             },
        #             {
        #                 "Effect": "Allow",
        #                 "Action": [
        #                     "iot:Publish"
        #                 ],
        #                 "Resource": [f"arn:aws:iot:{self.region}:{self.account}:topic/{topic_parameter.value_as_string}"]
        #             },
        #             {
        #                 "Effect": "Allow",
        #                 "Action": [
        #                     "iot:Subscribe"
        #                 ],
        #                 "Resource": [f"arn:aws:iot:{self.region}:{self.account}:topicfilter/{topic_parameter.value_as_string}"]
        #             },
        #             {
        #                 "Effect": "Allow",
        #                 "Action": [
        #                     "iot:Receive"
        #                 ],
        #                 "Resource": [f"arn:aws:iot:{self.region}:{self.account}:topic/{topic_parameter.value_as_string}"]
        #             }
        #         ]
        #     }
        # )




        
        
        # Lambda function for certificate creation
        lambda_path = os.path.join(os.path.dirname(__file__), "lambda")
        cert_handler = lambda_.Function(
            self, "CreateCertLambda",
            runtime=lambda_.Runtime.PYTHON_3_12,
            timeout=Duration.minutes(5),
            handler="create_cert.handler",
            code=lambda_.Code.from_asset(lambda_path),
            environment={
                "CERTIFICATE_SSM_PARAM": f"/iot/{thing_name}/certificate",
                "PRIVATE_KEY_SSM_PARAM": f"/iot/{thing_name}/private-key",
                "PUBLIC_KEY_SSM_PARAM": f"/iot/{thing_name}/public-key",
                "THING_NAME": thing_name,
                "IOT_TOPIC": topic_parameter.value_as_string,
                "IOT_POLICY": f"{thing_name}-policy",
                "REGION": self.region,
                "ACCOUNT": self.account
            },
           
            # Disable the default role creation with managed policy
            role=iam.Role(
                self, "CreateCertLambdaRole",
                assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
                inline_policies={
                    "CloudWatchLogsPolicy": iam.PolicyDocument(
                        statements=[
                            iam.PolicyStatement(
                                actions=[
                                    "logs:CreateLogGroup",
                                    "logs:CreateLogStream",
                                    "logs:PutLogEvents"
                                ],
                                resources=[
                                    f"arn:aws:logs:{self.region}:{self.account}:log-group:/aws/lambda/*"
                                ]
                            )
                        ]
                    )
                }
            )
        )




        # Add SSM permissions to Lambda
        cert_handler.add_to_role_policy(iam.PolicyStatement(
            actions=[
                "ssm:PutParameter",
                "ssm:DeleteParameter"
            ],
            resources=[
                f"arn:aws:ssm:{self.region}:{self.account}:parameter/iot/{thing_name}/*"
            ]
        ))




        # Add IoT permissions to Lambda with more specific resource scoping
        cert_handler.add_to_role_policy(iam.PolicyStatement(
            actions=[
                "iot:CreateKeysAndCertificate"
            ],
            resources=["*"]  # This specific API doesn't support resource-level permissions
        ))



        # Add IoT permissions with resource-level restrictions
        cert_handler.add_to_role_policy(iam.PolicyStatement(
            actions=[
                "iot:AttachPolicy",
                "iot:DetachPolicy"
            ],
            resources=[
                f"arn:aws:iot:{self.region}:{self.account}:policy/{thing_name}-policy",
                 f"arn:aws:iot:{self.region}:{self.account}:cert/*"
            ]
        ))

        cert_handler.add_to_role_policy(iam.PolicyStatement(
            actions=[
                "iot:AttachThingPrincipal",
                "iot:DetachThingPrincipal",
                "iot:DescribeThing",
                "iot:DeleteThing",
                "iot:CreateThing"
            ],
            resources=[
                f"arn:aws:iot:{self.region}:{self.account}:thing/{thing_name}",
                 f"arn:aws:iot:{self.region}:{self.account}:cert/*"
            ]
        ))

        cert_handler.add_to_role_policy(iam.PolicyStatement(
            actions=[
                "iot:UpdateCertificate",
                "iot:DeleteCertificate",
                "iot:DescribeCertificate"
            ],
            resources=[
                f"arn:aws:iot:{self.region}:{self.account}:cert/*"
            ]
        ))



        cert_handler.add_to_role_policy(iam.PolicyStatement(
            actions=[
                "iot:ListAttachedPolicies",
                "iot:ListPrincipalThings",
                "iot:ListThingPrincipals"
            ],
            resources=[
                f"arn:aws:iot:{self.region}:{self.account}:*"
            ]
        ))

        # Add IoT policy permissions to Lambda
        cert_handler.add_to_role_policy(iam.PolicyStatement(
            actions=[
                "iot:CreatePolicy",
                "iot:GetPolicy",
                "iot:DeletePolicy",
                "iot:ListPolicyVersions",
                "iot:DeletePolicyVersion"
            ],
            resources=[
                f"arn:aws:iot:{self.region}:{self.account}:policy/{thing_name}-policy"
            ]
        ))




        # Create custom resource
        cert_resource = CustomResource(
            self, "CertificateResource",
            removal_policy=RemovalPolicy.RETAIN,
            service_token=cr.Provider(
                self, "CertProvider",
                on_event_handler=cert_handler
            ).service_token
        )




        # Outputs
        CfnOutput(
            self, "ThingNameOutput",
            value=thing_name,
            description="IoT Thing Name",
            export_name="IoTThingName-Export"
        )
        
        CfnOutput(
            self, "CertificateArn",
            value=cert_resource.get_att_string("certificateArn"),
            description="Certificate ARN"
        )

        CfnOutput(
            self, "CertificateSSMParameter",
            value=cert_resource.get_att_string("certificateParameter"),
            description="SSM Parameter containing the Certificate PEM"
        )

        CfnOutput(
            self, "PrivateKeySSMParameter",
            value=cert_resource.get_att_string("privateKeyParameter"),
            description="SSM Parameter containing the Private Key"
        )

        CfnOutput(
            self, "PublicKeySSMParameter",
            value=cert_resource.get_att_string("publicKeyParameter"),
            description="SSM Parameter containing the Public Key"
        )

        # Create VPC
        vpc = ec2.Vpc(
            self, "IoTDeviceVPC",
            max_azs=2,
            nat_gateways=0,
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="public",
                    subnet_type=ec2.SubnetType.PUBLIC,
                )
            ]
        )



        # Create EC2 Role
        ec2_role = iam.Role(
            self, "EC2Role",
            assumed_by=iam.ServicePrincipal("ec2.amazonaws.com"),
        )

        # Add SSM permissions to EC2 role to read parameters
        ec2_role.add_to_policy(iam.PolicyStatement(
            actions=[
                "ssm:GetParameter",
            ],
            resources=[
                f"arn:aws:ssm:{self.region}:{self.account}:parameter/iot/{thing_name}/*"
            ]
        ))




        # Add S3 permissions using the parameter
        s3_policy = iam.PolicyStatement(
            sid="S3BucketAccess",  # Add a statement ID for better identification
            actions=[
                "s3:GetObject",
                "s3:ListBucket"
            ],
            resources=[
                f"arn:aws:s3:::{bucket_parameter.value_as_string}",
                f"arn:aws:s3:::{bucket_parameter.value_as_string}/*"
            ]
        )
        ec2_role.add_to_policy(s3_policy)



        # get AWS IoT endpoint
       
        ec2_role.add_to_policy(iam.PolicyStatement(
            actions=[
                "iot:DescribeEndpoint"
            ],
            resources=["*"],
            sid="AllowIoTDescribeEndpoint"  # Add a statement ID for better identification
        ))



        # Create User Data script to set up certificates
        # Modify user data to include downloading files from S3
        user_data = ec2.UserData.for_linux()
        user_data.add_commands(
            "yum update -y",
            "yum install -y aws-cli jq unzip python3 python3-pip",
            
            # Create necessary directories
            "mkdir -p /home/ec2-user/certs",
            "mkdir -p /home/ec2-user/device_code",
            
            # Download root CA certificate
            "curl -o /home/ec2-user/certs/AmazonRootCA1.pem https://www.amazontrust.com/repository/AmazonRootCA1.pem",
            
            # Get certificates from SSM and save them
            f"""aws ssm get-parameter --name "/iot/{thing_name}/certificate" --with-decryption --region {self.region} \
                | jq -r '.Parameter.Value' > /home/ec2-user/certs/device.pem.crt""",
            f"""aws ssm get-parameter --name "/iot/{thing_name}/private-key" --with-decryption --region {self.region} \
                | jq -r '.Parameter.Value' > /home/ec2-user/certs/private.pem.key""",
            f"""aws ssm get-parameter --name "/iot/{thing_name}/public-key" --with-decryption --region {self.region} \
                | jq -r '.Parameter.Value' > /home/ec2-user/certs/public.pem.key""",
            
            # Download and extract device code
            f"aws s3 cp {device_code.s3_object_url} /tmp/device_code.zip",
            "cd /home/ec2-user/device_code && unzip -o /tmp/device_code.zip",
            "rm /tmp/device_code.zip",
            f"export AWS_DEFAULT_REGION={self.region}",
            
            # Set proper ownership and permissions
            "chown -R ec2-user:ec2-user /home/ec2-user/certs",
            "chown -R ec2-user:ec2-user /home/ec2-user/device_code",
            "chmod 700 /home/ec2-user/certs",
            "chmod 600 /home/ec2-user/certs/*",
            
            # Install Python requirements if requirements.txt exists
            "if [ -f /home/ec2-user/device_code/requirements.txt ]; then",
            "pip3 install -r /home/ec2-user/device_code/requirements.txt",
            "pip3 install awsiotsdk --ignore-installed awscrt",
            "pip3 install boto3",
            f"export AWS_DEFAULT_REGION={self.region}"
            "fi",
                        )

        

        # Create EC2 Instance
        instance = ec2.Instance(
            self, "IoTDevice",
            vpc=vpc,
            instance_type=ec2.InstanceType.of(
                ec2.InstanceClass.T3, 
                ec2.InstanceSize.MICRO
            ),
            machine_image=ec2.AmazonLinuxImage(
                generation=ec2.AmazonLinuxGeneration.AMAZON_LINUX_2023
            ),
            role=ec2_role,
            user_data=user_data,
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PUBLIC
            ),
        )



        # Grant S3 read permissions to EC2 role for the asset bucket
        device_code.grant_read(instance.role)


        # Add EC2 instance outputs
        CfnOutput(
            self, "InstanceId",
            value=instance.instance_id,
            description="EC2 Instance ID"
        )

        CfnOutput(
            self, "InstancePublicIP",
            value=instance.instance_public_ip,
            description="EC2 Instance Public IP"
        )

        CfnOutput(
            self, "TopicNameOutput",
            value=topic_parameter.value_as_string,
            description="IoT Topic Name",
            export_name="IoTTopicName-Export"
        )

        # CfnOutput(
        #     self, "SSHCommand",
        #     value=f"ssh -i your-key.pem ec2-user@{instance.instance_public_ip}",
        #     description="SSH Command"
        # )
