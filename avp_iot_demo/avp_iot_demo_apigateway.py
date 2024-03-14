import os
import yaml
from string import Template
from types import SimpleNamespace
from typing import Any
from aws_cdk import (
    aws_apigateway as apigateway,
)
from constructs import Construct


class OpenApiVariableMapping(SimpleNamespace):
    cors_allow_origin: str
    user_actions_lambda_arn: str
    lambda_authorizer_arn: str


class AvpIotDemoApiGateway(Construct):

    def __init__(
        self,
            scope: Construct,
            construct_id: str,
            cors_allow_origin: str,
            user_actions_lambda_arn: str,
            lambda_authorizer_arn: str,
            **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Get the OpenAPI spec from a YAML template as a dictionary
        openapi_spec = self.__get_openapi_spec(
            f'{os.path.join(os.path.dirname(__file__), "..", "openapi-spec.yaml")}',
            OpenApiVariableMapping(
                cors_allow_origin=cors_allow_origin,
                user_actions_lambda_arn=user_actions_lambda_arn,
                lambda_authorizer_arn=lambda_authorizer_arn
            ))

        # Create an API Gateway REST API from the OpenAPI spec
        self._apigateway = apigateway.SpecRestApi(
            self, "avp-iot-demo-api",
            api_definition=apigateway.ApiDefinition.from_inline(openapi_spec)
        )

    @property
    def apigateway(self) -> apigateway.SpecRestApi:
        return self._apigateway

    def __get_openapi_spec(cls, path: str, var_mapping: OpenApiVariableMapping) -> Any:
        """
        Get the OpenAPI spec from a template file.
        :param path: Path to the template file.
        :param var_mapping: A mapping of variables to replace in the template.
        :return: The OpenAPI spec as a dictionary.
        :raises: FileNotFoundError if the template file is not found.
        :raises: yaml.YAMLError if the template file is invalid YAML.
        """
        class OpenApiYamlTemplate(Template):
            delimiter = '$'
            idpattern = None
            braceidpattern = r'(?a:[_a-z][_a-z0-9]*)'

        with open(path, 'r') as file:
            data = file.read()
            template = OpenApiYamlTemplate(data)
            openapi_spec_as_str = template.safe_substitute(
                var_mapping.__dict__)

        return yaml.safe_load(openapi_spec_as_str)
