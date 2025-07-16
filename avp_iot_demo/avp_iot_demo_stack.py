from aws_cdk import Stack, CfnOutput, Fn
from constructs import Construct


from avp_iot_demo.policy_store.policy_store_construct import AvpPolicyStore
from avp_iot_demo.constructs.apigateway_construct import AvpIotDemoApiGateway
from avp_iot_demo.constructs.cognito_construct import CognitoConstruct
from avp_iot_demo.constructs.lambda_construct import Lambdas

class AvpIotDemoStack(Stack):
    def __init__(
        self, scope: Construct, construct_id: str, config_path: str, **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        cognito = CognitoConstruct(self, "CognitoConstruct")
        user_pool_id = cognito.user_pool.user_pool_id

        policy_store = AvpPolicyStore(
            self, "AvpIoTDemoPolicyStore", user_pool_id=user_pool_id
        )

        # Import thing name from IoT stack
        thing_name = Fn.import_value("IoTThingName-Export")
        iot_topic = Fn.import_value("IoTTopicName-Export")

        lambdas = Lambdas(
            self,
            "DemoLambdas",
            policy_store_id=policy_store.policy_store_id,
            thing_name=thing_name,
            iot_topic=iot_topic,
        )

        apigateway = AvpIotDemoApiGateway(
            self,
            "AvpIotDemoApi",
            cors_allow_origin="http://localhost:3000",
            devices_lambda_arn=lambdas.devices_integration_arn,  # For /devices endpoint
            download_lambda_arn=lambdas.download_integration_arn,  # For /download endpoint
            role_lambda_arn=lambdas.role_integration_arn,  # For /role endpoint
            lambda_authorizer_arn=lambdas.authorizer_arn,  # protects /devices and /download enpoints
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

        CfnOutput(
            self,
            "CognitoUserPoolId",
            value=cognito.cognito_user_pool_id,
            description="User Pool ID",
            export_name="CognitoUserPoolId",
        )

        CfnOutput(
            self,
            "CognitoClientId",
            value=cognito.cognito_client_id,
            description="User Client ID",
            export_name="CognitoClientId",
        )
