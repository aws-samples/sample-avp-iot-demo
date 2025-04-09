import json
import base64
import os

def lambda_handler(event, context):
    print(f"Received event: {event}")
    
    try:
        bearer_token = event.get('headers', {}).get('Authorization') or event.get('headers', {}).get('authorization')
        if not bearer_token:
            raise ValueError("Authorization header is missing")
        
        print(f"Extracted bearer token (masked): {bearer_token[:10]}...")
        
        if bearer_token.lower().startswith('bearer '):
            bearer_token = bearer_token.split(' ')[1]
            print("Bearer prefix removed from token")
        
        token_payload = bearer_token.split('.')[1]
        padding = '=' * (-len(token_payload) % 4)
        parsed_token = json.loads(
            base64.b64decode(token_payload + padding).decode('utf-8')
        )
        print(f"Parsed token payload: {parsed_token}")
        
        groups = parsed_token.get('cognito:groups', [])
        
        if not groups:
            return {
                'statusCode': 200,
                'body': json.dumps({'message': 'User does not belong to any group'})
            }
        
        # Assuming a user belongs to only one group, return the first group
        user_group = groups[0]
        
        return {
            'statusCode': 200,
            'body': json.dumps({'group': user_group})
        }
    
    except ValueError as ve:
        print(f"ValueError: {str(ve)}")
        return {
            'statusCode': 400,
            'body': json.dumps({'error': str(ve)})
        }
    except json.JSONDecodeError as je:
        print(f"JSONDecodeError: {str(je)}")
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'Invalid token format'})
        }
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Internal server error'})
        }
