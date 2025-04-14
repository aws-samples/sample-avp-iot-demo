import json
import boto3
import os
from datetime import datetime, timezone

def lambda_handler(event, context):
    # Define CORS headers
    headers = {
        'Access-Control-Allow-Origin': '*',  # TODO: use Amplify domain
        'Access-Control-Allow-Headers': 'Content-Type,Authorization,X-Amz-Date,X-Api-Key,X-Amz-Security-Token',
        'Access-Control-Allow-Methods': 'POST,OPTIONS',
        'Access-Control-Allow-Credentials': 'true'
    }

    # Extract s3Path from authorizer context
    try:
        authorizer_context = event['requestContext']['authorizer']
        s3Path = authorizer_context.get('s3Path', '')
        print(f"S3 path: {s3Path}")
    except Exception as e:
        print(f"Error extracting s3Path from authorizer context: {str(e)}")
        s3Path = "s3://test"  # fallback value for now
    
    print(f"Extracted s3Path: {s3Path}")
    
    iotDevice = os.environ['IOT_THING_NAME']
    
    timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%SZ')
    
    message = {
        "timestamp": timestamp,
        "device": iotDevice,
        "s3Path": s3Path
    }
    
    iot_client = boto3.client('iot-data')
    
    try:
        response = iot_client.publish(
            topic='my/custom/topic',  # Adjust for IoT topic
            qos=1,
            payload=json.dumps(message)
        )
        
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({
                'message': 'Successfully published to IoT Core',
                'data': message
            })
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({
                'error': str(e)
            })
        }
