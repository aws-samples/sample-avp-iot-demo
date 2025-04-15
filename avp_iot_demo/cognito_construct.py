# lib/cognito_construct.py
from aws_cdk import CfnOutput, aws_cognito as cognito
from constructs import Construct

class CognitoConstruct(Construct):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create the user pool
        self.user_pool = cognito.UserPool(
            self, 
            "UserPool",
            user_pool_name="avp-iot-user-pool",
            self_sign_up_enabled=True,
            sign_in_aliases=cognito.SignInAliases(
                email=True,
                username=False
            ),
            standard_attributes=cognito.StandardAttributes(
                email=cognito.StandardAttribute(
                    required=True,
                    mutable=True
                )
            ),
            password_policy=cognito.PasswordPolicy(
                min_length=8,
                require_lowercase=True,
                require_uppercase=True,
                require_digits=True,
                require_symbols=True
            )
        )

        # Create user pool client
        self.client = self.user_pool.add_client(
            "avp-iot-client",
            auth_flows=cognito.AuthFlow(
                admin_user_password=True,
                user_password=True,
                user_srp=True
            ),
            o_auth=cognito.OAuthSettings(
                flows=cognito.OAuthFlows(
                    authorization_code_grant=True
                ),
                scopes=[cognito.OAuthScope.EMAIL, cognito.OAuthScope.OPENID, cognito.OAuthScope.PROFILE, cognito.OAuthScope.COGNITO_ADMIN],
                callback_urls=["http://localhost:3000"],  # Don't think we need these 
                logout_urls=["http://localhost:3000"]
            )
        )

        # Create groups
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
    
    @property
    def cognito_user_pool_id(self) -> str:
        return self.user_pool.user_pool_id

    @property
    def cognito_client_id(self) -> str:
        return self.client.user_pool_client_id
    


