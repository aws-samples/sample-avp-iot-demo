from aws_cdk import Stack, CfnOutput, aws_lambda as _lambda, aws_iam as iam
from constructs import Construct


class Lambdas(Construct):
    def __init__(self, scope: Construct, id: str, policy_store_id: str, thing_name: str) -> None:
        super().__init__(scope, id)

        # no longer needed, keeping it in case we change our minds
        # layer = _lambda.LayerVersion(
        #     self,
        #     "AuthorizerLayer",
        #     code=_lambda.Code.from_asset("lambdas/layers/python.zip"),
        #     compatible_runtimes=[_lambda.Runtime.PYTHON_3_11],
        #     description="JWT layer for Authorizer function",
        # )

        self.authorizer_function = _lambda.Function(
            self,
            "AuthorizerFunction",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="index.lambda_handler",
            code=_lambda.Code.from_asset("lambdas/authorizer"),
            # layers=[layer],
            environment={
                "POLICY_STORE_ID": policy_store_id,
                "TOKEN_TYPE": "identityToken",
                "NAMESPACE": "AvpIotDemoApi",
            },
        )

        self.devices_integration_fn = _lambda.Function(
            self,
            "DevicesIntegrationFunction",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="devices.lambda_handler",
            code=_lambda.Code.from_asset("lambdas/integration"),
        )

        self.download_integration_fn = _lambda.Function(
            self,
            "DownloadIntegrationFunction",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="download.lambda_handler",
            code=_lambda.Code.from_asset("lambdas/integration"),
            environment={
                "IOT_THING_NAME": thing_name,
            },
        )

        self.role_integration_fn = _lambda.Function(
            self,
            "RoleIntegrationFunction",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="role.lambda_handler",
            code=_lambda.Code.from_asset("lambdas/integration"),
        )

        self.authorizer_function.add_to_role_policy(
            iam.PolicyStatement(
                actions=["verifiedpermissions:IsAuthorizedWithToken"],
                resources=[
                    f"arn:aws:verifiedpermissions::{Stack.of(self).account}:policy-store/{policy_store_id}"
                ],
            )
        )

        self.devices_integration_fn.add_to_role_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW, actions=["iot:ListThings"], resources=["*"]
            )
        )

        self.download_integration_fn.add_to_role_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=["iot:Publish"],
                resources=[
                    f"arn:aws:iot:{Stack.of(self).region}:{Stack.of(self).account}:topic/*"  # TODO: restrict
                ],
            )
        )

        for function in [
            self.authorizer_function,
            self.devices_integration_fn,
            self.download_integration_fn,
            self.role_integration_fn,
        ]:
            function.add_to_role_policy(
                iam.PolicyStatement(
                    actions=[
                        "logs:CreateLogGroup",
                        "logs:CreateLogStream",
                        "logs:PutLogEvents",
                    ],
                    resources=["*"],
                )
            )

        self.authorizer_function.grant_invoke(
            iam.ServicePrincipal("apigateway.amazonaws.com")
        )
        self.devices_integration_fn.grant_invoke(
            iam.ServicePrincipal("apigateway.amazonaws.com")
        )
        self.download_integration_fn.grant_invoke(
            iam.ServicePrincipal("apigateway.amazonaws.com")
        )
        self.role_integration_fn.grant_invoke(
            iam.ServicePrincipal("apigateway.amazonaws.com")
        )

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
