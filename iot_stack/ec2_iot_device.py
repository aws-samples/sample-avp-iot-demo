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
    Duration
)
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

        

         # Define the IP address parameter
        ssh_ip_parameter = CfnParameter(
            self, "SSHAccessIP",
            type="String",
            description="IP address allowed to SSH to the EC2 instance (CIDR format, e.g., 192.168.1.0/24)",
            allowed_pattern="^(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])(\\/([0-9]|[1-2][0-9]|3[0-2]))$",
            constraint_description="Must be a valid IP CIDR range of the form x.x.x.x/x"
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

        # Define the IoT Policy
        iot_policy = iot.CfnPolicy(
            self, "IoTPolicy",
            policy_name="avp-iot-policy",
            policy_document={
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Action": [
                            "iot:Connect",
                            "iot:Publish",
                            "iot:Subscribe",
                            "iot:Receive"
                        ],
                        "Resource": ["*"]
                    }
                ]
            }
        )

        # Create IoT Thing
        thing = iot.CfnThing(
            self, "IoTThing",
            thing_name="avp-iot-device"
        )

        # Lambda function for certificate creation
        lambda_path = os.path.join(os.path.dirname(__file__), "lambda")
        cert_handler = lambda_.Function(
            self, "CreateCertLambda",
            runtime=lambda_.Runtime.PYTHON_3_9,
            timeout=Duration.minutes(3),
            handler="create_cert.handler",
            code=lambda_.Code.from_asset(lambda_path),
            environment={
                "CERTIFICATE_SSM_PARAM": f"/iot/{thing.thing_name}/certificate",
                "PRIVATE_KEY_SSM_PARAM": f"/iot/{thing.thing_name}/private-key",
                "PUBLIC_KEY_SSM_PARAM": f"/iot/{thing.thing_name}/public-key"
            }
        )

        # Add SSM permissions to Lambda
        cert_handler.add_to_role_policy(iam.PolicyStatement(
            actions=[
                "ssm:PutParameter",
                "ssm:DeleteParameter"
            ],
            resources=[
                f"arn:aws:ssm:{self.region}:{self.account}:parameter/iot/{thing.thing_name}/*"
            ]
        ))

        # Add IoT permissions to Lambda
        cert_handler.add_to_role_policy(iam.PolicyStatement(
            actions=[
                "iot:CreateKeysAndCertificate",
                "iot:AttachPolicy",
                "iot:AttachThingPrincipal",
                "iot:DetachPolicy",
                "iot:DetachThingPrincipal",
                "iot:UpdateCertificate",
                "iot:DeleteCertificate"
            ],
            resources=["*"]
        ))

        # Create custom resource
        cert_resource = CustomResource(
            self, "CertificateResource",
            service_token=cr.Provider(
                self, "CertProvider",
                on_event_handler=cert_handler
            ).service_token
        )

        # Outputs
        CfnOutput(
            self, "ThingName",
            value=thing.thing_name,
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
                f"arn:aws:ssm:{self.region}:{self.account}:parameter/iot/{thing.thing_name}/*"
            ]
        ))

        # Add S3 permissions using the parameter
        ec2_role.add_to_policy(iam.PolicyStatement(
            actions=[
                "s3:GetObject",
                "s3:ListBucket"
            ],
            resources=[
                f"arn:aws:s3:::{bucket_parameter.value_as_string}",
                f"arn:aws:s3:::{bucket_parameter.value_as_string}/*"
            ]
        ))

        # get AWS IoT endpoint
        ec2_role.add_to_policy(iam.PolicyStatement(
            actions=[
                "iot:DescribeEndpoint"
            ],
            resources=["*"]
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
            f"""aws ssm get-parameter --name "/iot/{thing.thing_name}/certificate" --with-decryption --region {self.region} \
                | jq -r '.Parameter.Value' > /home/ec2-user/certs/device.pem.crt""",
            f"""aws ssm get-parameter --name "/iot/{thing.thing_name}/private-key" --with-decryption --region {self.region} \
                | jq -r '.Parameter.Value' > /home/ec2-user/certs/private.pem.key""",
            f"""aws ssm get-parameter --name "/iot/{thing.thing_name}/public-key" --with-decryption --region {self.region} \
                | jq -r '.Parameter.Value' > /home/ec2-user/certs/public.pem.key""",
            
            # Download and extract device code
            f"aws s3 cp {device_code.s3_object_url} /tmp/device_code.zip",
            "cd /home/ec2-user/device_code && unzip -o /tmp/device_code.zip",
            "rm /tmp/device_code.zip",
            f"export AWS_DEFAULT_REGION={self.region}"
            
            # Set proper ownership and permissions
            "chown -R ec2-user:ec2-user /home/ec2-user/certs",
            "chown -R ec2-user:ec2-user /home/ec2-user/device_code",
            "chmod 700 /home/ec2-user/certs",
            "chmod 600 /home/ec2-user/certs/*",
            
            # Install Python requirements if requirements.txt exists
            "if [ -f /home/ec2-user/device_code/requirements.txt ]; then",
            "pip3 install -r /home/ec2-user/device_code/requirements.txt",
            "pip3 install awsiotsdk --ignore-installed awscrt"
            "pip3 install boto3"
            "fi",
            
            # # Create systemd service for the subscriber
            # f"""cat << 'EOF' > /etc/systemd/system/iot-subscriber.service
            #         [Unit]
            #         Description=IoT Subscriber Service
            #         After=network.target

            #         [Service]
            #         Type=simple
            #         User=ec2-user
            #         WorkingDirectory=/home/ec2-user/device_code
            #         ExecStart=/usr/bin/python3 /home/ec2-user/device_code/local_subscribe.py --topic "{topic_parameter.value_as_string}"
            #         Restart=always
            #         RestartSec=5

            #         [Install]
            #         WantedBy=multi-user.target
            #         EOF""",

            #                 # Enable and start the service
            #                 "systemctl enable iot-subscriber",
            #                 "systemctl start iot-subscriber"
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

        # Modify the security group rule to use the parameter
        instance.connections.allow_from(
            ec2.Peer.ipv4(ssh_ip_parameter.value_as_string),
            ec2.Port.tcp(22),
            description="Allow SSH from specified IP"
        )

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

        # CfnOutput(
        #     self, "SSHCommand",
        #     value=f"ssh -i your-key.pem ec2-user@{instance.instance_public_ip}",
        #     description="SSH Command"
        # )