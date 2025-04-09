import json
import base64
import os
import boto3
from urllib.parse import parse_qs

policy_store_id = os.environ['POLICY_STORE_ID']
namespace = os.environ['NAMESPACE']
token_type = os.environ['TOKEN_TYPE']
resource_type = f"{namespace}::Application"
resource_id = namespace
action_type = f"{namespace}::Action"

print(f"Environment variables loaded: POLICY_STORE_ID={policy_store_id}, NAMESPACE={namespace}, TOKEN_TYPE={token_type}")
print(f"Derived variables: resource_type={resource_type}, resource_id={resource_id}, action_type={action_type}")

verifiedpermissions = boto3.client('verifiedpermissions')

def lambda_handler(event, context):
    print(f"Received event: {event}")
    
    try:
        bearer_token = event.get('headers', {}).get('Authorization') or event.get('headers', {}).get('authorization')
        print(f"Extracted bearer token (masked): {bearer_token[:10]}...")
        
        if bearer_token and bearer_token.lower().startswith('bearer '):
            bearer_token = bearer_token.split(' ')[1]
            print("Bearer prefix removed from token")
            
        token_payload = bearer_token.split('.')[1]
        padding = '=' * (-len(token_payload) % 4)
        parsed_token = json.loads(
            base64.b64decode(token_payload + padding).decode('utf-8')
        )
        print(f"Parsed token payload: {parsed_token}")
        
        action_id = f"{event['requestContext']['httpMethod'].lower()} {event['requestContext']['resourcePath']}"
        print(f"Constructed action_id: {action_id}")
        
        input_params = {
            token_type: bearer_token,
            'policyStoreId': policy_store_id,
            'action': {
                'actionType': action_type,
                'actionId': action_id
            },
            'resource': {
                'entityType': resource_type,
                'entityId': resource_id
            }
        }
            
        print("Calling verifiedpermissions.is_authorized_with_token...")
        auth_response = verifiedpermissions.is_authorized_with_token(**input_params)
        print(f"AVP decision: {auth_response}")
        
        principal_id = f"{parsed_token['iss'].split('/')[3]}|{parsed_token['sub']}"
        print(f"Initial principal_id: {principal_id}")
        
        if 'principal' in auth_response:
            principal_eid_obj = auth_response['principal']
            principal_id = f"{principal_eid_obj['entityType']}::\"{principal_eid_obj['entityId']}\""
            print(f"Updated principal_id: {principal_id}")
        
        # Extract s3Path from query string parameters
        query_params = event.get('queryStringParameters', {}) or {}
        s3_path = query_params.get('s3Path', '')
        print(f"S3 Path from query parameters: {s3_path}")
        
        response = {
            'principalId': principal_id,
            'policyDocument': {
                'Version': '2012-10-17',
                'Statement': [{
                    'Action': 'execute-api:Invoke',
                    'Effect': 'Allow' if auth_response['decision'].upper() == 'ALLOW' else 'Deny',
                    'Resource': event['methodArn']
                }]
            },
            'context': {
                'actionId': action_id,
                's3Path': s3_path  # Pass s3Path to the integration Lambda
            }
        }
        print(f"Final response: {response}")
        return response
        
    except Exception as e:
        print(f"Error occurred: {str(e)}")
        print(f"Error type: {type(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        
        deny_response = {
            'principalId': '',
            'policyDocument': {
                'Version': '2012-10-17',
                'Statement': [{
                    'Action': 'execute-api:Invoke',
                    'Effect': 'Deny',
                    'Resource': event['methodArn']
                }]
            },
            'context': {}
        }
        print(f"Returning deny response: {json.dumps(deny_response, indent=2)}")
        return deny_response
