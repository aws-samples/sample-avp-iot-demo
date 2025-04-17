import json
import boto3
from botocore.exceptions import ClientError

def lambda_handler(event, context):
    iot_client = boto3.client('iot')
    
    try:
        response = iot_client.list_things()
        things = response['things']
        
        return {
            'statusCode': 200,
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
            'body': json.dumps({
                'error': error_message,
                'type': 'ClientError'
            })
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e),
                'type': 'GeneralException'
            })
        }
