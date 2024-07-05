# atlassian-backup
A repository to hold the files for the FT CT Atlassian backup on colab.research.google.com Jupyter Notebooks automated solution.

## How is GColab Used Here
Google Colab, or Colaboratory, is a free Jupyter Notebook environment provided by Google. It allows you to write and execute Python code through your browser, leveraging the power of Google's cloud infrastructure. Here’s how Google Colab utilizes Jupyter Notebooks:

## What are Jupyter Notebooks?

![Gcolab](https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcS01sXsOua7q1xxpoMn9N0JA0npthSFCtffxQ&usqp=CAU)


Jupyter Notebooks are an open-source web application that allows you to create and share documents that contain live code, equations, visualizations, and narrative text. They are widely used in data science, scientific computing, and machine learning for interactive data analysis and visualizations. The name "Jupyter" comes from the core programming languages it supports: Julia, Python, and R.

## Key Features

- **Interactive Code Execution**: Write and execute code in a variety of programming languages, most commonly Python.
- **Data Visualization**: Easily create and display visualizations using libraries like Matplotlib, Seaborn, and Plotly.
- **Rich Text**: Combine code with Markdown text, which can include HTML and LaTeX for mathematical equations.
- **Document Sharing**: Share notebooks with others through platforms like GitHub or export them to formats like HTML, PDF, and slides.

## Why Use Jupyter Notebooks?

1. **Ease of Use**: The user-friendly interface makes it simple to write and run code in small, manageable chunks called cells.
2. **Reproducibility**: Notebooks capture the entire data analysis process, making it easy to reproduce and share with others.
3. **Integration**: Jupyter Notebooks integrate with numerous data science tools and libraries, making it a versatile choice for various tasks.
4. **Visualization**: With built-in support for rich media, it's easy to visualize data and create interactive plots and graphs.


# Google Colab Script for Automating File Downloads and Google Drive Uploads

![Gcolab](https://miro.medium.com/v2/resize:fit:986/1*pimj8lXWwZnqLs2xVCV2Aw.png)

This guide explains a script designed for use on [Google Colab](https://colab.research.google.com/). The script automates the download of files from a specific URL and uploads them to Google Drive. Follow the steps below to understand the functionality of each part of the script.

## Prerequisites

1. **Library Installation**: Make sure to install the required library by running:
    ```python
    !pip install schedule
    ```

2. **Imports**: The script imports several necessary libraries:
    ```python
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
    ```

## Script Overview

1. **Variables Initialization**: 
    - `PRINCIPAL`, `BASE_URL`, `DOWNLOAD_URL`, and `PROGRESS_URL` are URLs specific to your use case.
    - `EMAIL` and `API_KEY` should be populated with your credentials.
    ```python
    PRINCIPAL = 'financialtimes'
    BASE_URL = f'https://{PRINCIPAL}.atlassian.net/wiki'
    DOWNLOAD_URL = f'{BASE_URL}/download/temp/filestore/'
    PROGRESS_URL = f'{BASE_URL}/rest/obm/1.0/getprogress.json'
    EMAIL = ''
    API_KEY = ''
    ```

2. **Mount Google Drive**: 
    ```python
    drive.mount('/content/drive')
    ```

3. **Authenticate and Create Drive Service**: 
    ```python
    auth.authenticate_user()
    drive_service = build('drive', 'v3', cache_discovery=False)
    ```

4. **Fetch File Information**: 
    ```python
    def get_file_info():
        try:
            auth = (EMAIL, API_KEY)
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
    ```

5. **Create or Get Folder in Google Drive**: 
    ```python
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
    ```

6. **Download and Upload File to Google Drive**: 
    ```python
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
    ```

7. **Check for Last Friday of the Month**: 
    ```python
    def is_last_friday_of_month(date):
        next_friday = date + timedelta((4 - date.weekday()) % 7)
        return next_friday.month != date.month
    ```

8. **Job Scheduler**: 
    ```python
    def job():
        today = datetime.today()
        if is_last_friday_of_month(today):
            folder_path = './'  # Replace with desired Google Drive folder path
            file_id, _ = get_file_info()
            download_to_drive(file_id, folder_path)
    ```

## Example Usage

- **Immediate Execution**: Uncomment the following lines to run the download immediately.
    ```python
    folder_path = './'  # Replace with desired Google Drive folder path
    file_id, alt_percentage = get_file_info()
    download_to_drive(file_id, folder_path)
    ```

- **Scheduled Execution**: Uncomment the following lines to schedule the job to run every Friday at 10:00 AM.
    ```python
    def schedule_job():
        schedule.every().friday.at("10:00").do(job)
        while True:
            schedule.run_pending()
            time.sleep(60)

    schedule_job()
    ```

This guide should help you understand the script step-by-step and configure it for your own use.
