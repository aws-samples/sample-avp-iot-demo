from aws_cdk import Stack, CfnOutput
from constructs import Construct


from avp_iot_demo.apigateway_construct import AvpIotDemoApiGateway
from avp_iot_demo.policy_store.policy_store_construct import AvpPolicyStore
from avp_iot_demo.s3_construct import IoTDeviceFilesS3Bucket
from avp_iot_demo.lambda_construct import Lambdas
from avp_iot_demo.cognito_construct import CognitoConstruct


class AvpIotDemoStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        cognito = CognitoConstruct(self, "CognitoConstruct")

        policy_store = AvpPolicyStore(self, "AvpIoTDemoPolicyStore", user_pool_id=cognito.user_pool_id)
        policy_store.node.add_dependency(cognito)

        lambdas = Lambdas(self, "DemoLambdas", policy_store_id=policy_store.policy_store_id)

        apigateway = AvpIotDemoApiGateway(
            self,
            "AvpIotDemoApi",
            cors_allow_origin="http://localhost:3000",
            devices_lambda_arn=lambdas.devices_integration_arn,  # For /devices endpoint
            download_lambda_arn=lambdas.download_integration_arn,  # For /download endpoint
            role_lambda_arn=lambdas.role_integration_arn, # For /role endpoint
            lambda_authorizer_arn=lambdas.authorizer_arn,
        )


        CfnOutput(
            self,
            "ApiGatewayEndpoint",
            value=apigateway.api_endpoint,
            description="API Gateway Endpoint",
            export_name="ApiGatewayEndpoint",
        )

        CfnOutput(
            self,
            "ApiGatewayId",
            value=apigateway.api_id,
            description="API Gateway ID",
            export_name="ApiGatewayId",
        )

        is_deploy_sample_files = bool(
            self.node.try_get_context("mock-data/deploySampleIoTDeviceFilesToS3")
            == "true"
        )

        IoTDeviceFilesS3Bucket(
            self,
            "AvpIotDemoDeviceFilesS3Bucket",
            deploy_sample_files=is_deploy_sample_files,
        )
