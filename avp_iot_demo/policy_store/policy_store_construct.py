import os
from types import SimpleNamespace
from aws_cdk import (
    aws_verifiedpermissions as verifiedpermissions
)
from constructs import Construct

from utils.string_utils import file_to_string


class _MockPolicyVariableMapping(SimpleNamespace):
    manager_role_id: str
    operator_role_id: str


class AvpPolicyStore(Construct):

    def __init__(
        self,
            scope: Construct,
            construct_id: str,
            **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # create policy store in Amazon Verified Permissions
        schema_json_str = file_to_string(
            f'{os.path.join(os.path.dirname(__file__), "cedarschema.json")}',
        )
        cfn_policy_store = verifiedpermissions.CfnPolicyStore(
            self, "AvpIotDemoPolicyStore",
            validation_settings=verifiedpermissions.CfnPolicyStore.ValidationSettingsProperty(
                mode="STRICT"
            ),
            description="Policy store for AVP IoT Demo",
            schema=verifiedpermissions.CfnPolicyStore.SchemaDefinitionProperty(
                cedar_json=schema_json_str
            )
        )
        self._policy_store_id = cfn_policy_store.attr_policy_store_id

        # create policy for users to list role actions
        common_role_policy = file_to_string(
            f'{os.path.join(os.path.dirname(__file__), "common.role.cedar")}',
        )
        self.__create_policy(
            "CommonRolePolicy",
            statement=common_role_policy,
            description="List assigned role's actions for any user"
        )

        # create mock policies for manager and operator roles
        policy_var_mapping = _MockPolicyVariableMapping(
            manager_role_id=self.node.try_get_context(
                'mock-data/managerRoleId'),
            operator_role_id=self.node.try_get_context(
                'mock-data/operatorRoleId'),
        )

        manager_device_policy = file_to_string(
            f'{os.path.join(os.path.dirname(__file__), "manager.device.cedar")}',
            var_mapping=policy_var_mapping)
        manager_file_policy = file_to_string(
            f'{os.path.join(os.path.dirname(__file__), "manager.file.cedar")}',
            var_mapping=policy_var_mapping)
        operator_device_policy = file_to_string(
            f'{os.path.join(os.path.dirname(__file__), "operator.device.cedar")}',
            var_mapping=policy_var_mapping)
        operator_file_policy = file_to_string(
            f'{os.path.join(os.path.dirname(__file__), "operator.file.cedar")}',
            var_mapping=policy_var_mapping)
        self.__create_policy(
            "ManagerDevicePolicy",
            statement=manager_device_policy,
            description="Allow manager to read/write devices"
        )
        self.__create_policy(
            "ManagerFilePolicy",
            statement=manager_file_policy,
            description="Allow manager to read files"
        )
        self.__create_policy(
            "OperatorDevicePolicy",
            statement=operator_device_policy,
            description="Allow operator to read devices"
        )
        self.__create_policy(
            "OperatorFilePolicy",
            statement=operator_file_policy,
            description="Allow operator to read files"
        )

    @property
    def policy_store_id(self) -> str:
        return self._policy_store_id

    def __create_policy(self, id: str, statement: str, description: str) -> None:
        verifiedpermissions.CfnPolicy(
            self, id,
            policy_store_id=self._policy_store_id,
            definition=verifiedpermissions.CfnPolicy.PolicyDefinitionProperty(
                static=verifiedpermissions.CfnPolicy.StaticPolicyDefinitionProperty(
                    statement=statement,
                    description=description
                ),
            ))
