import os
from aws_cdk import aws_verifiedpermissions as verifiedpermissions, CfnOutput, Stack
from constructs import Construct
from utils.string_utils import file_to_string


class AvpPolicyStore(Construct):
    def __init__(
        self, scope: Construct, construct_id: str, user_pool_id: str, **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create policy store
        schema_json_str = file_to_string(
            f'{os.path.join(os.path.dirname(__file__), "cedarschema.json")}',
        )
        cfn_policy_store = verifiedpermissions.CfnPolicyStore(
            self,
            "AvpIotDemoPolicyStore",
            validation_settings=verifiedpermissions.CfnPolicyStore.ValidationSettingsProperty(
                mode="STRICT"
            ),
            description="Policy store for AVP IoT Demo",
            schema=verifiedpermissions.CfnPolicyStore.SchemaDefinitionProperty(
                cedar_json=schema_json_str
            ),
        )
        self._policy_store_id = cfn_policy_store.attr_policy_store_id

        # Add Cognito Identity Source
        identity_source = verifiedpermissions.CfnIdentitySource(
            self,
            "CognitoIdentitySource",
            configuration=verifiedpermissions.CfnIdentitySource.IdentitySourceConfigurationProperty(
                cognito_user_pool_configuration=verifiedpermissions.CfnIdentitySource.CognitoUserPoolConfigurationProperty(
                    user_pool_arn=f"arn:aws:cognito-idp:us-east-1:{Stack.of(self).account}:userpool/{user_pool_id}",
                )
            ),
            policy_store_id=self._policy_store_id,
            principal_entity_type="AvpIotDemoApi::User",
        )

        identity_source.add_override(
            "Properties.Configuration.CognitoUserPoolConfiguration.GroupConfiguration",
            {"GroupEntityType": "AvpIotDemoApi::UserGroup"},
        )

        # Ensure identity source is created after policy store
        identity_source.node.add_dependency(cfn_policy_store)

        manager_policy_statement = f"""permit (
            principal in AvpIotDemoApi::UserGroup::"{user_pool_id}|manager",
            action in [
                AvpIotDemoApi::Action::"get /devices",
                AvpIotDemoApi::Action::"post /download"
            ],
            resource
        );"""

        # Operator policy statement
        operator_policy_statement = f"""permit (
            principal in AvpIotDemoApi::UserGroup::"{user_pool_id}|operator",
            action in [
                AvpIotDemoApi::Action::"get /devices"
            ],
            resource
        );"""

        # Create manager policy
        manager_policy = verifiedpermissions.CfnPolicy(
            self,
            "ManagerPolicy",
            policy_store_id=self._policy_store_id,
            definition=verifiedpermissions.CfnPolicy.PolicyDefinitionProperty(
                static=verifiedpermissions.CfnPolicy.StaticPolicyDefinitionProperty(
                    statement=manager_policy_statement
                )
            ),
        )

        # Create operator policy
        operator_policy = verifiedpermissions.CfnPolicy(
            self,
            "OperatorPolicy",
            policy_store_id=self._policy_store_id,
            definition=verifiedpermissions.CfnPolicy.PolicyDefinitionProperty(
                static=verifiedpermissions.CfnPolicy.StaticPolicyDefinitionProperty(
                    statement=operator_policy_statement
                )
            ),
        )

        manager_policy.node.add_dependency(cfn_policy_store)
        operator_policy.node.add_dependency(cfn_policy_store)

        # Output the policy store ID
        CfnOutput(
            self,
            "PolicyStoreId",
            value=self._policy_store_id,
            description="ID of the created policy store",
        )

    @property
    def policy_store_id(self) -> str:
        return self._policy_store_id
