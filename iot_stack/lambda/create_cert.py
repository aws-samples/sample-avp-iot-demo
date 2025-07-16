import boto3
import json
import urllib3
import logging
import os

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def handler(event, context):
    logger.info('Event: %s', event)
    
    physical_id = event.get('PhysicalResourceId', 'NotYetCreated')
    request_type = event['RequestType']
    
    # Get SSM parameter names from environment variables
    cert_param_name = os.environ['CERTIFICATE_SSM_PARAM']
    private_key_param_name = os.environ['PRIVATE_KEY_SSM_PARAM']
    public_key_param_name = os.environ['PUBLIC_KEY_SSM_PARAM']
    thing_name = os.environ['THING_NAME']
    policy_name = f"{thing_name}-policy"
    
    try:
        response_data = {}
        ssm = boto3.client('ssm')
        iot = boto3.client('iot')
        
        if request_type in ['Create', 'Update']:
            # Create IoT policy first
            try:
                # Check if policy already exists
                iot.get_policy(policyName=policy_name)
                logger.info(f"Policy '{policy_name}' already exists")
            except iot.exceptions.ResourceNotFoundException:
                # Create the policy if it doesn't exist
                # Get the AWS region and account ID from the Lambda context
                region = context.invoked_function_arn.split(":")[3]
                account_id = context.invoked_function_arn.split(":")[4]
                
                # Get the topic name from environment variable or use a default
                # In a real implementation, you might want to pass this as a parameter
                topic = os.environ.get('IOT_TOPIC', 'my/topic/name')
                
                policy_document = {
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Effect": "Allow",
                            "Action": [
                                "iot:Connect"
                            ],
                            "Resource": [f"arn:aws:iot:{region}:{account_id}:client/{thing_name}"]
                        },
                        {
                            "Effect": "Allow",
                            "Action": [
                                "iot:Publish"
                            ],
                            "Resource": [f"arn:aws:iot:{region}:{account_id}:topic/{topic}"]
                        },
                        {
                            "Effect": "Allow",
                            "Action": [
                                "iot:Subscribe"
                            ],
                            "Resource": [f"arn:aws:iot:{region}:{account_id}:topicfilter/{topic}"]
                        },
                        {
                            "Effect": "Allow",
                            "Action": [
                                "iot:Receive"
                            ],
                            "Resource": [f"arn:aws:iot:{region}:{account_id}:topic/{topic}"]
                        }
                    ]
                }
                
                policy_response = iot.create_policy(
                    policyName=policy_name,
                    policyDocument=json.dumps(policy_document)
                )
                logger.info(f"Created new IoT policy: {policy_name}")
            
            # Create IoT thing
            try:
                # Check if thing already exists
                iot.describe_thing(thingName=thing_name)
                logger.info(f"Thing '{thing_name}' already exists")
            except iot.exceptions.ResourceNotFoundException:
                # Create the thing if it doesn't exist
                thing_response = iot.create_thing(
                    thingName=thing_name,
                )
                logger.info("Created new IoT thing: %s", thing_response['thingName'])
            
            # Create certificate
            cert_response = iot.create_keys_and_certificate(setAsActive=True)
            
            # Store certificate and keys in SSM Parameter Store
            ssm.put_parameter(
                Name=cert_param_name,
                Value=cert_response['certificatePem'],
                Type='SecureString',
                Overwrite=True
            )
            
            ssm.put_parameter(
                Name=private_key_param_name,
                Value=cert_response['keyPair']['PrivateKey'],
                Type='SecureString',
                Overwrite=True
            )
            
            ssm.put_parameter(
                Name=public_key_param_name,
                Value=cert_response['keyPair']['PublicKey'],
                Type='SecureString',
                Overwrite=True
            )
            
            # Attach policy to certificate
            iot.attach_policy(
                policyName=policy_name,
                target=cert_response['certificateArn']
            )
            
            # Attach thing to certificate
            iot.attach_thing_principal(
                thingName=thing_name,
                principal=cert_response['certificateArn']
            )
            
            response_data = {
                'certificateArn': cert_response['certificateArn'],
                'certificateId': cert_response['certificateId'],
                'certificateParameter': cert_param_name,
                'privateKeyParameter': private_key_param_name,
                'publicKeyParameter': public_key_param_name,
                'thingName': thing_name
            }
            
            physical_id = cert_response['certificateArn']

            
        elif request_type == 'Delete':
            if physical_id != 'NotYetCreated':
                cert_arn = physical_id
                cert_id = cert_arn.split('/')[-1]

                try:
                    # First list all principals attached to the thing
                    principals = iot.list_thing_principals(
                        thingName=thing_name
                    )['principals']

                    # Detach all principals from the thing
                    for principal in principals:
                        try:
                            iot.detach_thing_principal(
                                thingName=thing_name,
                                principal=principal
                            )
                            logger.info(f"Successfully detached principal {principal} from thing")
                        except Exception as e:
                            logger.error(f"Error detaching principal {principal}: {str(e)}")

                    # List and detach all policies from the certificate
                    try:
                        attached_policies = iot.list_attached_policies(
                            target=cert_arn
                        )['policies']
                        
                        for policy in attached_policies:
                            iot.detach_policy(
                                policyName=policy['policyName'],
                                target=cert_arn
                            )
                            
                            # Delete the policy
                            try:
                                iot.delete_policy(
                                    policyName=policy['policyName']
                                )
                                logger.info(f"Successfully deleted policy {policy['policyName']}")
                            except Exception as e:
                                logger.error(f"Error deleting policy {policy['policyName']}: {str(e)}")
                                
                    except Exception as e:
                        logger.error(f"Error detaching policies: {str(e)}")

                    # Deactivate the certificate
                    iot.update_certificate(
                        certificateId=cert_id,
                        newStatus='INACTIVE'
                    )

                    # Delete the certificate
                    iot.delete_certificate(
                        certificateId=cert_id,
                        forceDelete=True
                    )

                    # Clean up SSM parameters
                    ssm = boto3.client('ssm')
                    for param_name in [cert_param_name, private_key_param_name, public_key_param_name]:
                        try:
                            ssm.delete_parameter(Name=param_name)
                        except ssm.exceptions.ParameterNotFound:
                            pass
                            
                    # Delete the IoT thing as the last step
                    try:
                        iot.delete_thing(thingName=thing_name)
                        logger.info(f"Successfully deleted IoT thing '{thing_name}'")
                    except Exception as e:
                        logger.error(f"Error deleting IoT thing: {str(e)}")

                except Exception as e:
                    logger.error(f"Error during cleanup: {str(e)}")
                    raise Exception(f"Failed to clean up resources: {str(e)}")


        
        response = {
            'Status': 'SUCCESS',
            'PhysicalResourceId': physical_id,
            'StackId': event['StackId'],
            'RequestId': event['RequestId'],
            'LogicalResourceId': event['LogicalResourceId'],
            'Data': response_data
        }
        
    except Exception as e:
        logger.error('Error: %s', str(e))
        response = {
            'Status': 'FAILED',
            'PhysicalResourceId': physical_id,
            'StackId': event['StackId'],
            'RequestId': event['RequestId'],
            'LogicalResourceId': event['LogicalResourceId'],
            'Reason': str(e)
        }
    
    response_url = event['ResponseURL']
    json_response = json.dumps(response)
    
    http = urllib3.PoolManager()
    try:
        http.request(
            'PUT',
            response_url,
            body=json_response,
            headers={'Content-Type': 'application/json'}
        )
    except Exception as e:
        logger.error('Failed to send response to CloudFormation: %s', str(e))
        raise
    
    return response
