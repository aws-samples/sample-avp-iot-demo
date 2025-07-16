import json
import os
import sys

def read_cdk_outputs():
    """Read the CDK outputs from outputs.json"""
    try:
        # Navigate up one directory from utils to find outputs.json
        script_dir = os.path.dirname(os.path.abspath(__file__))
        outputs_path = os.path.join(script_dir, '..', 'outputs.json')
        outputs_path = os.path.normpath(outputs_path)

        with open(outputs_path, 'r') as f:
            outputs = json.load(f)

        # get values from AvpIotDemoStack
        stack_outputs = outputs['AvpIotDemoStack']
        return {
            'api_url': stack_outputs['ApiGatewayEndpoint'],
            'user_pool_id': stack_outputs['CognitoUserPoolId'],
            'client_id': stack_outputs['CognitoClientId']
        }
    except FileNotFoundError:
        print(f"Error: outputs.json not found at {outputs_path}")
        sys.exit(1)
    except KeyError as e:
        print(f"Error: Missing required key in outputs.json: {e}")
        sys.exit(1)
    except json.JSONDecodeError:
        print("Error: Invalid JSON in outputs.json")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading outputs.json: {str(e)}")
        sys.exit(1)

def update_files(env_file_path, amplify_outputs_path):
    try:
        print("Reading values from outputs.json...")
        values = read_cdk_outputs()
        
        # Attempt to update .env.local file
        try:
            with open(env_file_path, 'r') as f:
                env_content = f.read()
            
            updated_env_content = env_content.replace('API_URL=API_URL_FROM_OUTPUTS', f'API_URL={values["api_url"]}')
            
            with open(env_file_path, 'w') as f:
                f.write(updated_env_content)
                
            print(f"\nSuccessfully updated {env_file_path} with API Gateway URL")
            print(f"API URL: {values['api_url']}")
        except Exception as e:
            print(f"Error updating .env.local: {str(e)}")
            sys.exit(1)

        # Attempt to update amplify_outputs.json file
        try:
            with open(amplify_outputs_path, 'r') as f:
                amplify_outputs = json.load(f)
            
            # Update user_pool_id and user_pool_client_id
            amplify_outputs['auth']['user_pool_id'] = values['user_pool_id']
            amplify_outputs['auth']['user_pool_client_id'] = values['client_id']
            
            with open(amplify_outputs_path, 'w') as f:
                json.dump(amplify_outputs, f, indent=2)
                
            print(f"\nSuccessfully updated {amplify_outputs_path} with:")
            print(f"User Pool ID: {values['user_pool_id']}")
            print(f"Client ID: {values['client_id']}")
        except Exception as e:
            print(f"Error updating amplify_outputs.json: {str(e)}")
            sys.exit(1)

    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)

def create_env_file(env_file_path):
    """Create a new .env.local file with default template"""
    try:    
        # Create .env.local with default content
        with open(env_file_path, 'w') as f:
            f.write('API_URL=API_URL_FROM_OUTPUTS\n')
        print(f"Created new {env_file_path} file with default template")
    except Exception as e:
        print(f"Error creating {env_file_path}: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    env_file_path = os.path.join(script_dir, '..', 'web_app', '.env.local')
    amplify_outputs_path = os.path.join(script_dir, '..', 'web_app', 'amplify_outputs.json')
    
    env_file_path = os.path.normpath(env_file_path)
    amplify_outputs_path = os.path.normpath(amplify_outputs_path)
    
    # Create .env.local if it doesn't exist
    if not os.path.exists(env_file_path):
        print(f".env.local not found, creating it...")
        create_env_file(env_file_path)
    
    # Verify amplify_outputs.json exists
    if not os.path.exists(amplify_outputs_path):
        print(f"Error: {amplify_outputs_path} does not exist")
        sys.exit(1)
        
    update_files(env_file_path, amplify_outputs_path)

