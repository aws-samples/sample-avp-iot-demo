# lib/cognito_construct.py
from aws_cdk import CfnOutput, aws_cognito as cognito
from constructs import Construct

class CognitoConstruct(Construct):
    def __init__(self, scope: Construct, construct_id: str, user_pool_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Import the existing user pool
        self.user_pool = cognito.UserPool.from_user_pool_id(
            self,
            "ExistingUserPool",
            user_pool_id=user_pool_id
        )
        
        # Create operator group
        operator_group = cognito.CfnUserPoolGroup(
            self,
            "OperatorGroup",
            user_pool_id=user_pool_id,
            group_name="operator",
            description="Group for operators"
        )

        # Create manager group
        manager_group = cognito.CfnUserPoolGroup(
            self,
            "ManagerGroup",
            user_pool_id=user_pool_id,
            group_name="manager",
            description="Group for managers"
        )

        # Create app client = I don't think we need this but keeping it for now
        # self.app_client = cognito.UserPoolClient(
        #     self,
        #     "AvpIotDemoAppClient",
        #     user_pool=self.user_pool,
        #     generate_secret=True,
        #     auth_flows=cognito.AuthFlow(
        #         user_password=True,
        #         user_srp=True
        #     )
        # )

        CfnOutput(self, "UserPoolId", value=user_pool_id)
        # CfnOutput(self, "UserPoolClientId", value=self.app_client.user_pool_client_id)

    @property
    def user_pool_id(self) -> str:
        return self.user_pool.user_pool_id

    # @property
    # def client_id(self) -> str:
    #     return self.app_client.user_pool_client_id
