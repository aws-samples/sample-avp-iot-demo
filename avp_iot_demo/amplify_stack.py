from aws_cdk import (
    Stack,
    CfnOutput,
    aws_amplify as amplify,
)
from constructs import Construct


class AmplifyStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        amplify_app = amplify.CfnApp(
            self,
            "MyAmplifyApp",
            name="my-amplify-app",
            platform="WEB_COMPUTE",  # This specifies Amplify Gen 2
            environment_variables=[
                amplify.CfnApp.EnvironmentVariableProperty(
                    name="AMPLIFY_MONOREPO_APP_ROOT", value="/"
                ),
                amplify.CfnApp.EnvironmentVariableProperty(
                    name="AMPLIFY_DIFF_DEPLOY", value="false"
                ),
            ],
            iam_service_role="AmplifySSRLoggingRole-0fac581d-95ae-45b3-8229-a395a4d47ff0"
        )

        amplify.CfnBranch(
            self,
            "MainBranch",
            app_id=amplify_app.attr_app_id,
            branch_name="main",
            enable_auto_build=True,
            framework="Next.js",
            stage="PRODUCTION",
        )

        amplify.CfnBranch(
            self,
            "DevBranch",
            app_id=amplify_app.attr_app_id,
            branch_name="dev",
            enable_auto_build=True,
            framework="Next.js",
            stage="DEVELOPMENT",
        )

        CfnOutput(
            self,
            "AmplifyAppId",
            value=amplify_app.attr_app_id,
            description="Amplify App ID",
        )
