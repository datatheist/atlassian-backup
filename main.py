import requests
import os
from datetime import datetime
import boto3
import sys

# Confluence details
REGION_NAME='eu-west-1'
PRINCIPAL = ''
BASE_URL = f'https://{PRINCIPAL}.atlassian.net/wiki'
PROGRESS_URL = f'{BASE_URL}/rest/obm/1.0/getprogress.json'
EMAIL = ''
API_KEY = ''
EC2_INSTANCE_ID = ''
# AWS details
S3_BUCKET = ''

def get_file_id():
    try:
        # Set up basic authentication
        auth = (EMAIL, API_KEY)
        
        # Fetch JSON data
        response = requests.get(PROGRESS_URL, auth=auth)
        response.raise_for_status()
        
        data = response.json()
        file_id = data.get('fileName')
        alt_percentage = data.get('alternativePercentage')
       
        if file_id:
            return file_id, alt_percentage
        else:
            raise Exception('fileName not found in JSON response')
    
    except requests.exceptions.RequestException as e:
        print(f'Request failed: {str(e)}')
    except Exception as e:
        print(f'An error occurred: {str(e)}')

def download_confluence_backup():
    try:
        # Get the file ID
        file_id, alt_percentage = get_file_id()
        print(alt_percentage)
        print(f'The file ID: {file_id}')
        if not file_id:
            print("Failing because of an empty file_id variable.")
            return
        
        auth = (EMAIL, API_KEY)
        # Construct the download URL
        download_url = f'{BASE_URL}/download/temp/filestore/{file_id}'

        # Set up basic authentication

        # Download the file from Confluence in streaming mode
        with requests.get(download_url, auth=auth, stream=True) as response:
            response.raise_for_status()
            # Get the total file size from the headers:
            total_size = int(response.headers.get('content-length', 0))
            # Define the file name with current date and time
            current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_name = f'confluence_backup_v1_{current_time}.zip'
            file_path = f'/home/ubuntu/confluence_backup/{file_name}'
            downloaded_size = 0


            # Save the file locally in chunks
            with open(file_path, 'wb') as file:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:  # Filter out keep-alive new chunks
                        file.write(chunk)
                        downloaded_size += len(chunk)
                        progress_percentage = (downloaded_size / total_size) * 100
                        print(f'\rDownloaded {downloaded_size / (1024 * 1024):.2f} MB of {total_size / (1024 * 1024):.2f} MB ({progress_percentage:.2f}%)', end='')
                        sys.stdout.flush()


            # Verify the downloaded file size
            downloaded_size = os.path.getsize(file_path)
            print(f'Downloaded file size: {downloaded_size / (1024 * 1024)} MB')

            # Print a portion of the file content to inspect
            with open(file_path, 'rb') as file:
                print("File content preview:")
                print(file.read(100))  # Read and print the first 100 bytes

            print('File downloaded successfully.')

            # Upload the file to S3
            s3 = boto3.client('s3')
            s3.upload_file(file_path, S3_BUCKET, file_name)
            print(f'File uploaded to S3: s3://{S3_BUCKET}/{file_name}')
            print('Shutting down the instance now...')
            stop_ec2_instance(EC2_INSTANCE_ID, REGION_NAME)


    except requests.exceptions.RequestException as e:
        print(f'Request failed: {str(e)}')
    except Exception as e:
        print(f'An error occurred: {str(e)}')


def stop_ec2_instance(instance_id, region):
    try:
        ec2 = boto3.client('ec2', region_name=region)
        response = ec2.stop_instances(InstanceIds=[instance_id])
        print(f'Stopping instance {instance_id}: {response}')
    except Exception as e:
        print(f'Failed to stop instance: {str(e)}')



# Calling the function
download_confluence_backup()
