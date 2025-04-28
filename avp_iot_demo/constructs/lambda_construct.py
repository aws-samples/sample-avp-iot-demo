from aws_cdk import Stack, CfnOutput, aws_lambda as _lambda, aws_iam as iam
from constructs import Construct


class Lambdas(Construct):
    def __init__(self, scope: Construct, id: str, policy_store_id: str, thing_name: str, iot_topic: str) -> None:
        super().__init__(scope, id)

        # Create custom roles for each Lambda function
        authorizer_role = self._create_authorizer_role(policy_store_id)
        devices_role = self._create_devices_role()
        download_role = self._create_download_role(iot_topic)
        role_integration_role = self._create_role_integration_role()

        self.authorizer_function = _lambda.Function(
            self,
            "AuthorizerFunction",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="index.lambda_handler",
            code=_lambda.Code.from_asset("lambdas/authorizer"),
            environment={
                "POLICY_STORE_ID": policy_store_id,
                "TOKEN_TYPE": "identityToken",
                "NAMESPACE": "AvpIotDemoApi",
            },
            role=authorizer_role,
        )

        self.devices_integration_fn = _lambda.Function(
            self,
            "DevicesIntegrationFunction",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="devices.lambda_handler",
            code=_lambda.Code.from_asset("lambdas/integration"),
            role=devices_role,
        )

        self.download_integration_fn = _lambda.Function(
            self,
            "DownloadIntegrationFunction",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="download.lambda_handler",
            code=_lambda.Code.from_asset("lambdas/integration"),
            environment={
                "IOT_THING_NAME": thing_name,
                "IOT_TOPIC": iot_topic
            },
            role=download_role,
        )

        self.role_integration_fn = _lambda.Function(
            self,
            "RoleIntegrationFunction",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="role.lambda_handler",
            code=_lambda.Code.from_asset("lambdas/integration"),
            role=role_integration_role,
        )

        # Grant API Gateway invoke permissions
        self.authorizer_function.grant_invoke(iam.ServicePrincipal("apigateway.amazonaws.com"))
        self.devices_integration_fn.grant_invoke(iam.ServicePrincipal("apigateway.amazonaws.com"))
        self.download_integration_fn.grant_invoke(iam.ServicePrincipal("apigateway.amazonaws.com"))
        self.role_integration_fn.grant_invoke(iam.ServicePrincipal("apigateway.amazonaws.com"))
        
        # Create CloudFormation outputs
        self._create_outputs()

    def _create_authorizer_role(self, policy_store_id: str) -> iam.Role:
        """Create a custom role for the authorizer function"""
        role = iam.Role(
            self,
            "AuthorizerRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com")
        )
        
        # Add Verified Permissions policy
        role.add_to_policy(
            iam.PolicyStatement(
                actions=["verifiedpermissions:IsAuthorizedWithToken"],
                resources=[
                    f"arn:aws:verifiedpermissions::{Stack.of(self).account}:policy-store/{policy_store_id}"
                ],
            )
        )
        
        # Add CloudWatch Logs permissions
        role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "logs:CreateLogGroup",
                    "logs:CreateLogStream",
                    "logs:PutLogEvents",
                ],
                resources=[
                    f"arn:aws:logs:{Stack.of(self).region}:{Stack.of(self).account}:log-group:/aws/lambda/AuthorizerFunction*",
                ]
            )
        )
        
        return role
    
    def _create_devices_role(self) -> iam.Role:
        """Create a custom role for the devices integration function"""
        role = iam.Role(
            self,
            "DevicesRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com")
        )
        
        # Add IoT permissions
        role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW, 
                actions=["iot:ListThings"], 
                resources=[f"arn:aws:iot:{Stack.of(self).region}:{Stack.of(self).account}:*"]
            )
        )
        
        # Add CloudWatch Logs permissions
        role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "logs:CreateLogGroup",
                    "logs:CreateLogStream",
                    "logs:PutLogEvents",
                ],
                resources=[
                    f"arn:aws:logs:{Stack.of(self).region}:{Stack.of(self).account}:log-group:/aws/lambda/DevicesIntegrationFunction*",
                ]
            )
        )
        
        return role
    
    def _create_download_role(self, iot_topic: str) -> iam.Role:
        """Create a custom role for the download integration function"""
        role = iam.Role(
            self,
            "DownloadRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com")
        )
        
        # Add IoT publish permissions
        role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=["iot:Publish"],
                resources=[
                    f"arn:aws:iot:{Stack.of(self).region}:{Stack.of(self).account}:topic/{iot_topic}"
                ],
            )
        )
        
        # Add CloudWatch Logs permissions
        role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "logs:CreateLogGroup",
                    "logs:CreateLogStream",
                    "logs:PutLogEvents",
                ],
                resources=[
                    f"arn:aws:logs:{Stack.of(self).region}:{Stack.of(self).account}:log-group:/aws/lambda/DownloadIntegrationFunction*",
                ]
            )
        )
        
        return role
    
    def _create_role_integration_role(self) -> iam.Role:
        """Create a custom role for the role integration function"""
        role = iam.Role(
            self,
            "RoleIntegrationRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com")
        )
        
        # Add CloudWatch Logs permissions
        role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "logs:CreateLogGroup",
                    "logs:CreateLogStream",
                    "logs:PutLogEvents",
                ],
                resources=[
                    f"arn:aws:logs:{Stack.of(self).region}:{Stack.of(self).account}:log-group:/aws/lambda/RoleIntegrationFunction*",
                ]
            )
        )
        
        return role

    @property
    def authorizer_arn(self) -> str:
        return self.authorizer_function.function_arn

    @property
    def devices_integration_arn(self) -> str:
        return self.devices_integration_fn.function_arn

    @property
    def role_integration_arn(self) -> str:
        return self.role_integration_fn.function_arn

    @property
    def download_integration_arn(self) -> str:
        return self.download_integration_fn.function_arn
        
    # Add CloudFormation outputs
    def _create_outputs(self):
        """Create CloudFormation outputs for Lambda ARNs"""
        CfnOutput(
            self,
            "AuthorizerFunctionArn",
            value=self.authorizer_function.function_arn,
            description="ARN of the Authorizer function",
        )

        CfnOutput(
            self,
            "DevicesIntegrationFunctionArn",
            value=self.devices_integration_fn.function_arn,
            description="ARN of the Devices Integration function",
        )

        CfnOutput(
            self,
            "DownloadIntegrationFunctionArn",
            value=self.download_integration_fn.function_arn,
            description="ARN of the Download Integration function",
        )

        CfnOutput(
            self,
            "RoleIntegrationFunctionArn",
            value=self.role_integration_fn.function_arn,
            description="ARN of the Role Integration function",
        )
