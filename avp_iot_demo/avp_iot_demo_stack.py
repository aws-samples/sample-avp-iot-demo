from aws_cdk import (
    # Duration,
    Stack,
    # aws_sqs as sqs,
    aws_lambda as _lambda,
)
from constructs import Construct

from avp_iot_demo.apigateway_construct import AvpIotDemoApiGateway
from avp_iot_demo.policy_store.policy_store_construct import AvpPolicyStore


class AvpIotDemoStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # The code that defines your stack goes here

        # This Lambda function is only used to test deploying API Gateway using OpenAPI spec
        # TODO: use real Lambda function for API Gateway, if needed
        # TODO: change API Gateway integration in OpenAPI spec to AWS Services, if needed
        lambda_fn = _lambda.Function(
            self, "OpenApiSpecTestLambda",
            runtime=_lambda.Runtime.PYTHON_3_11,
            code=_lambda.Code.from_inline("""
def handler(event, context):
    return {
      statusCode: 200,
      body: json.dumps({"message": "hello world"})
    }
"""
                                          ),
            handler="lambda.handler"
        )

        apigateway = AvpIotDemoApiGateway(
            self,
            "AvpIotDemoApi",
            cors_allow_origin="http://localhost:3000",
            role_actions_lambda_arn=lambda_fn.function_arn,
            lambda_authorizer_arn=lambda_fn.function_arn,
        )

        policy_store = AvpPolicyStore(
            self,
            "AvpIoTDemoPolicyStore"
        )

        # example resource
        # queue = sqs.Queue(
        #     self, "AvpIotDemoQueue",
        #     visibility_timeout=Duration.seconds(300),
        # )
