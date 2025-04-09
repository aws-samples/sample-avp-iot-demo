# lib/cognito_construct.py
from aws_cdk import CfnOutput, aws_cognito as cognito
from constructs import Construct

class CognitoConstruct(Construct):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.user_pool = cognito.UserPool(
            self,
            "AvpIotDemoUserPool",
            user_pool_name="avp-iot-demo-user-pool",
            self_sign_up_enabled=True,
            auto_verify=cognito.AutoVerifiedAttrs(email=True),
            standard_attributes=cognito.StandardAttributes(
                email=cognito.StandardAttribute(required=True, mutable=False)
            ),
            password_policy=cognito.PasswordPolicy(
                min_length=8,
                require_lowercase=True,
                require_uppercase=True,
                require_digits=True,
                require_symbols=True,
            ),
        )
        
        operator_group = cognito.CfnUserPoolGroup(
            self,
            "OperatorGroup",
            user_pool_id=self.user_pool.user_pool_id,
            group_name="operator",
            description="Group for operators"
        )

        manager_group = cognito.CfnUserPoolGroup(
            self,
            "ManagerGroup",
            user_pool_id=self.user_pool.user_pool_id,
            group_name="manager",
            description="Group for managers"
        )

        self.app_client = self.user_pool.add_client(
            "avp-iot-demo-app-client",
            generate_secret=True,
            auth_flows=cognito.AuthFlow(user_password=True, user_srp=True),
        )

        CfnOutput(self, "UserPoolId", value=self.user_pool.user_pool_id)
        CfnOutput(self, "UserPoolClientId", value=self.app_client.user_pool_client_id)

    @property
    def user_pool_id(self) -> str:
        return self.user_pool.user_pool_id

    @property
    def client_id(self) -> str:
        return self.app_client.user_pool_client_id
