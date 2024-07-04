# This is to be used exclusively on: https://colab.research.google.com/
# Run pip install schedule first, to install the library prerequisite.
import requests
from google.colab import drive
from google.colab import auth
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import io
import os
from urllib.parse import urlparse, unquote
import schedule
import time
from datetime import datetime, timedelta

PRINCIPAL = 'financialtimes'
BASE_URL = f'https://{PRINCIPAL}.atlassian.net/wiki'
DOWNLOAD_URL = f'{BASE_URL}/download/temp/filestore/'
PROGRESS_URL = f'{BASE_URL}/rest/obm/1.0/getprogress.json'
EMAIL = ''
API_KEY = ''

# Mount Google Drive
drive.mount('/content/drive')

# Authenticate and create the Drive API service
auth.authenticate_user()
drive_service = build('drive', 'v3', cache_discovery=False)

def get_file_info():
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

def get_or_create_folder(folder_path):
    folders = folder_path.strip('/').split('/')
    parent_id = 'root'

    for folder in folders:
        query = f"name='{folder}' and mimeType='application/vnd.google-apps.folder' and '{parent_id}' in parents and trashed=false"
        results = drive_service.files().list(q=query, spaces='drive', fields='files(id, name)').execute()
        items = results.get('files', [])

        if not items:
            file_metadata = {
                'name': folder,
                'mimeType': 'application/vnd.google-apps.folder',
                'parents': [parent_id]
            }
            folder = drive_service.files().create(body=file_metadata, fields='id').execute()
            parent_id = folder.get('id')
        else:
            parent_id = items[0]['id']

    return parent_id

def download_to_drive(file_id, folder_path):
    url = f'{DOWNLOAD_URL}{file_id}'
    try:
        auth = (EMAIL, API_KEY)
        response = requests.head(url, auth=auth, allow_redirects=True)
        print(f"HEAD request response: {response.status_code}, headers: {response.headers}")

        if response.status_code == 403:
            print("Access forbidden. Please check your API key and permissions.")
            return

        with requests.get(url, auth=auth, stream=True) as response:
            response.raise_for_status()
            _, alt_percentage = get_file_info()
            print(f"Download progress: {alt_percentage}%")
            folder_id = get_or_create_folder(folder_path)

            file_content = io.BytesIO()
            total_size = int(response.headers.get('content-length', 0))
            chunk_size = 1024
            for data in response.iter_content(chunk_size):
                file_content.write(data)
                # Calculate and print progress
                done = int(50 * file_content.tell() / total_size)
                print(f"\r[{'=' * done}{' ' * (50 - done)}] {file_content.tell() * 100 // total_size}%", end='')

            file_content.seek(0)
            file_metadata = {'name': file_id, 'parents': [folder_id]}
            media = MediaIoBaseUpload(file_content,
                                      mimetype=response.headers.get('content-type'),
                                      resumable=True)

            file = drive_service.files().create(body=file_metadata,
                                                media_body=media,
                                                fields='id').execute()

            print(f'\nFile ID: {file.get("id")}')
            print(f'File "{file_id}" has been uploaded to Google Drive in the folder: {folder_path}')

    except requests.exceptions.RequestException as e:
        print(f"Error downloading the file: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")

def is_last_friday_of_month(date):
    next_friday = date + timedelta((4 - date.weekday()) % 7)
    return next_friday.month != date.month

def job():
    today = datetime.today()
    if is_last_friday_of_month(today):
        folder_path = './'  # Replace with desired Google Drive folder path
        file_id, _ = get_file_info()
        download_to_drive(file_id, folder_path)

# Example usage
folder_path = './'  # Replace with desired Google Drive folder path

# Uncomment the following line to run immediately
file_id, alt_percentage = get_file_info()
download_to_drive(file_id, folder_path)

# Scheduler function
# Uncomment the next lines to enable scheduling
# def schedule_job():
#     # Schedule the job to run every Friday at 10:00 AM
#     schedule.every().friday.at("10:00").do(job)
#     while True:
#         schedule.run_pending()
#         time.sleep(60)

# schedule_job()
