import json
import boto3
from botocore.exceptions import ClientError

def lambda_handler(event, context):
    iot_client = boto3.client('iot')
    
    # Define CORS headers
    headers = {
        'Access-Control-Allow-Origin': '*',  # TODO: use Amplify domain
        'Access-Control-Allow-Headers': 'Content-Type,Authorization,X-Amz-Date,X-Api-Key,X-Amz-Security-Token',
        'Access-Control-Allow-Methods': 'GET,OPTIONS',
        'Access-Control-Allow-Credentials': 'true'
    }
    
    try:
        response = iot_client.list_things()
        things = response['things']
        
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({
                'message': 'Successfully retrieved IoT things',
                'things': things
            })
        }
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        
        return {
            'statusCode': error_code,
            'headers': headers,
            'body': json.dumps({
                'error': error_message,
                'type': 'ClientError'
            })
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({
                'error': str(e),
                'type': 'GeneralException'
            })
        }
