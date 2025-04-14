# your_project/lambda/create_cert.py

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
    
    try:
        response_data = {}
        ssm = boto3.client('ssm')
        
        if request_type in ['Create', 'Update']:
            iot = boto3.client('iot')
            
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
                policyName='avp-iot-policy',
                target=cert_response['certificateArn']
            )
            
            # Attach thing to certificate
            iot.attach_thing_principal(
                thingName='avp-iot-device',
                principal=cert_response['certificateArn']
            )
            
            response_data = {
                'certificateArn': cert_response['certificateArn'],
                'certificateId': cert_response['certificateId'],
                'certificateParameter': cert_param_name,
                'privateKeyParameter': private_key_param_name,
                'publicKeyParameter': public_key_param_name
            }
            
            physical_id = cert_response['certificateArn']
            
        elif request_type == 'Delete':
            if physical_id != 'NotYetCreated':
                iot = boto3.client('iot')
                cert_arn = physical_id
                cert_id = cert_arn.split('/')[-1]

                try:
                    # First list all principals attached to the thing
                    principals = iot.list_thing_principals(
                        thingName='avp-iot-device'
                    )['principals']

                    # Detach all principals from the thing
                    for principal in principals:
                        try:
                            iot.detach_thing_principal(
                                thingName='avp-iot-device',
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
