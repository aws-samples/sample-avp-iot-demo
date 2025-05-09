import os
import yaml
from types import SimpleNamespace
from typing import Any
from aws_cdk import (
    aws_apigateway as apigateway,
    aws_logs as logs,
    RemovalPolicy,
)
from constructs import Construct

from utils.string_utils import file_to_string


class _OpenApiVariableMapping(SimpleNamespace):
    cors_allow_origin: str
    role_actions_lambda_arn: str
    lambda_authorizer_arn: str


class AvpIotDemoApiGateway(Construct):

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        cors_allow_origin: str,
        devices_lambda_arn: str,
        download_lambda_arn: str,
        role_lambda_arn: str,
        lambda_authorizer_arn: str,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create CloudWatch Logs group for API Gateway access logs
        log_group = logs.LogGroup(
            self,
            "ApiGatewayAccessLogs",
            log_group_name=f"/aws/apigateway/AvpIotDemoApi-access-logs",
            retention=logs.RetentionDays.ONE_WEEK,
            removal_policy=RemovalPolicy.DESTROY
        )
        
        # Get the OpenAPI spec from a YAML template as a dictionary
        openapi_spec = self.__get_openapi_spec(
            f'{os.path.join(os.path.dirname(__file__), "openapi-spec.yaml")}',
            _OpenApiVariableMapping(
                cors_allow_origin=cors_allow_origin,
                devices_lambda_arn=devices_lambda_arn,
                download_lambda_arn=download_lambda_arn,
                role_lambda_arn=role_lambda_arn,
                lambda_authorizer_arn=lambda_authorizer_arn,
            ),
        )

        # Create an API Gateway REST API from the OpenAPI spec
        self._apigateway = apigateway.SpecRestApi(
            self,
            "AvpIotDemoApi",
            api_definition=apigateway.ApiDefinition.from_inline(openapi_spec),
            # Enable access logging to the CloudWatch Logs group
            deploy_options=apigateway.StageOptions(
                stage_name="dev",
                access_log_destination=apigateway.LogGroupLogDestination(log_group),
                access_log_format=apigateway.AccessLogFormat.clf(),
            ),
            cloud_watch_role=True,
        )

    @property
    def api_endpoint(self) -> str:
        return self._apigateway.url

    @property
    def api_id(self) -> str:
        return self._apigateway.rest_api_id

    def __get_openapi_spec(cls, path: str, var_mapping: _OpenApiVariableMapping) -> Any:
        """
        Get the OpenAPI spec from a template file.
        :param path: Path to the template file.
        :param var_mapping: A mapping of variables to replace in the template.
        :return: The OpenAPI spec as a dictionary.
        :raises: FileNotFoundError if the template file is not found.
        :raises: yaml.YAMLError if the template file is invalid YAML.
        """
        openapi_spec_as_str = file_to_string(path, var_mapping)
        return yaml.safe_load(openapi_spec_as_str)
