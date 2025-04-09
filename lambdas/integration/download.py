import json
import boto3
from datetime import datetime, timezone

def lambda_handler(event, context):
    # Extract s3Path from authorizer context
    try:
        authorizer_context = event['requestContext']['authorizer']
        s3Path = authorizer_context.get('s3Path', '')
        print(f"S3 path: {s3Path}")
    except Exception as e:
        print(f"Error extracting s3Path from authorizer context: {str(e)}")
        s3Path = "s3://test"  # fallback value for now
    
    print(f"Extracted s3Path: {s3Path}")
    
    # TODO: grab this from IoT stack
    iotDevice = "testDevice"
    
    timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%SZ')
    
    message = {
        "timestamp": timestamp,
        "device": iotDevice,
        "s3Path": s3Path
    }
    
    iot_client = boto3.client('iot-data')
    
    try:
        response = iot_client.publish(
            topic='device/data',  # Adjust for IoT topic
            qos=1,
            payload=json.dumps(message)
        )
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Successfully published to IoT Core',
                'data': message
            })
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e)
            })
        }
