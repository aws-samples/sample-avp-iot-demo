import json
import boto3
import time
import os
from datetime import datetime
from awscrt import mqtt
from awsiot import mqtt_connection_builder
import argparse
from urllib.parse import urlparse


CERT_PATH = "/home/ec2-user/certs"
CERTIFICATE = os.path.join(CERT_PATH, "device.pem.crt")
PRIVATE_KEY = os.path.join(CERT_PATH, "private.pem.key")
ROOT_CA = os.path.join(CERT_PATH, "AmazonRootCA1.pem")


def get_current_region():
    """Get current AWS region using boto3 session"""
    try:
        session = boto3.Session()
        return session.region_name or \
               boto3.client('ec2').meta.region_name or \
               os.environ.get('AWS_DEFAULT_REGION', 'us-east-1')
    except Exception as e:
        print(f"Error getting region: {str(e)}")
        return 'us-east-1'

def get_iot_endpoint():
    """Get AWS IoT endpoint using boto3."""
    try:
        current_region = get_current_region()

        iot_client = boto3.client('iot', region_name=current_region)
        response = iot_client.describe_endpoint(
            endpointType='iot:Data-ATS'
        )
        return response['endpointAddress']
    except Exception as e:
        print(f"Error getting IoT endpoint: {str(e)}")
        raise

def parse_s3_uri(s3_uri):
    """Parse S3 URI into bucket and key."""
    parsed = urlparse(s3_uri)
    if parsed.scheme != "s3":
        raise ValueError("Invalid S3 URI scheme. Must start with 's3://'")
    bucket = parsed.netloc
    key = parsed.path.lstrip('/')
    return bucket, key

def download_from_s3(s3_uri, local_path):
    """Download file from S3."""
    try:
        bucket, key = parse_s3_uri(s3_uri)
        s3_client = boto3.client('s3')
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        
        print(f"Downloading {s3_uri} to {local_path}")
        s3_client.download_file(bucket, key, local_path)
        print(f"Successfully downloaded file to {local_path}")
        return True
    except Exception as e:
        print(f"Error downloading file: {str(e)}")
        return False

def on_connection_interrupted(connection, error, **kwargs):
    print(f"Connection interrupted. error: {error}")

def on_connection_resumed(connection, return_code, session_present, **kwargs):
    print(f"Connection resumed. return_code: {return_code} session_present: {session_present}")

def on_message_received(topic, payload, dup, qos, retain, **kwargs):
    """Callback when message is received."""
    try:
        # Parse the payload
        message = json.loads(payload.decode())
        print(f"Received message from topic '{topic}': {json.dumps(message, indent=2)}")

        # Extract information from payload
        device_id = message.get('iotdevice')
        timestamp = message.get('timestamp')
        s3_path = message.get('s3path')

        if not s3_path:
            print("No S3 path provided in message")
            return

        # Create local file path
        timestamp_obj = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%SZ")
        local_directory = f"/home/ec2-user/downloads/{device_id}/{timestamp_obj.strftime('%Y-%m-%d')}"
        filename = os.path.basename(s3_path)
        local_path = f"{local_directory}/{filename}"

        # Download the file
        download_from_s3(s3_path, local_path)

    except json.JSONDecodeError as e:
        print(f"Error decoding JSON payload: {str(e)}")
    except Exception as e:
        print(f"Error processing message: {str(e)}")

def main():
    # Parse arguments
    parser = argparse.ArgumentParser(description="IoT Core subscriber and S3 downloader")
    parser.add_argument('--topic', required=True, help='Topic to subscribe to')
    parser.add_argument('--client-id', default='ec2-subscriber',
                      help='Client ID for MQTT connection (default: ec2-subscriber)')

    args = parser.parse_args()

    # Verify certificate files exist
    for cert_file, cert_name in [
        (CERTIFICATE, "Certificate"),
        (PRIVATE_KEY, "Private key"),
        (ROOT_CA, "Root CA")
    ]:
        if not os.path.exists(cert_file):
            raise FileNotFoundError(f"{cert_name} not found at {cert_file}")

    # Get IoT endpoint
    print("Getting IoT endpoint...")
    endpoint = get_iot_endpoint()
    print(f"IoT endpoint: {endpoint}")

    # Create MQTT connection
    mqtt_connection = mqtt_connection_builder.mtls_from_path(
        endpoint=endpoint,
        cert_filepath=CERTIFICATE,
        pri_key_filepath=PRIVATE_KEY,
        ca_filepath=ROOT_CA,
        client_id=args.client_id,
        clean_session=False,
        keep_alive_secs=30,
        on_connection_interrupted=on_connection_interrupted,
        on_connection_resumed=on_connection_resumed
    )

    print("Connecting to AWS IoT Core...")
    connect_future = mqtt_connection.connect()
    connect_future.result()
    print("Connected!")

    print(f"Subscribing to topic: {args.topic}")
    subscribe_future, _ = mqtt_connection.subscribe(
        topic=args.topic,
        qos=mqtt.QoS.AT_LEAST_ONCE,
        callback=on_message_received
    )
    subscribe_future.result()
    print(f"Subscribed to topic: {args.topic}")

    # Keep the main thread alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Disconnecting...")
        disconnect_future = mqtt_connection.disconnect()
        disconnect_future.result()
        print("Disconnected!")

if __name__ == "__main__":
    main()


#python subscriber.py --topic "my/topic/name"

