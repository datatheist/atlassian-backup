# atlassian-backup
A repository to hold the files for the FT CT Atlassian backup AWS automated solution.

# Backup Automation Process using AWS Lambda, EC2, and Atlassian API

This document provides a detailed explanation of the automated backup process that involves AWS Lambda, an EC2 instance, the Atlassian API, and AWS S3 storage. 

## Overview

The objective of this setup is to automate the process of downloading backup files from Atlassian, storing them in an AWS S3 bucket, and then shutting down the EC2 instance used for this task.

## Architecture Components

![Confluence Backup on AWS](https://github.com/datatheist/atlassian-backup/blob/feat-aws/Confluence_Backup_on_AWS.jpeg?raw=true)

1. **AWS Lambda**: 
    - **Function**: Starts the EC2 instance.
    - **Trigger**: Can be configured to run on a schedule (e.g., every last Friday of the month).

2. **EC2 Instance**:
    - **AMI**: Ubuntu.
    - **Startup Script**: Installs prerequisites and prepares a virtual environment (VENV).
    - **Execution**: Runs a bash script which initiates the Python script to download the backup file.

3. **Python Script**:
    - **Libraries**: `boto3`, `requests`.
    - **Function**: Downloads the backup file from Atlassian and uploads it to an S3 bucket.
    - **API Interaction**: Sends a GET request to the Atlassian API to fetch the backup file.

4. **AWS S3 Bucket**:
    - **Storage**: Stores the downloaded backup file from the EC2 instance.
    - **Cleanup**: Deletes the original file from the EC2 instance after upload.

5. **Bash Script**:
    - **Execution**: Starts the Python script.
    - **Shutdown**: Shuts down the EC2 instance after the completion of all tasks.

## Detailed Process Flow

### Step 1: AWS Lambda Function
AWS Lambda is configured to start the EC2 instance at a scheduled time. The Lambda function sends a signal to the EC2 instance to boot up.

### Step 2: EC2 Instance Initialization
Upon startup, the EC2 instance runs a script to:
1. Install necessary prerequisites.
2. Prepare a virtual environment.
3. Mount Google Drive (if required).
4. Authenticate and create the Drive API service.

### Step 3: Running the Python Script
The bash script initiates the Python script (`main.py`), which performs the following steps:

#### 3.1: Fetch File Information
The Python script uses the Atlassian API to fetch information about the file to be downloaded:
- **Endpoint**: `{BASE_URL}/rest/obm/1.0/getprogress.json`
- **Response**: JSON containing `fileName` and `alternativePercentage`.

#### 3.2: Download the File
The script constructs the download URL using the `fileName` obtained from the previous step and downloads the file in chunks, displaying the progress percentage.

#### 3.3: Upload to S3
Once the download is complete, the script uploads the file to a specified S3 bucket using the `boto3` library.

#### 3.4: Clean Up
After a successful upload, the script deletes the original file from the EC2 instance to free up space.

### Step 4: Shutting Down the EC2 Instance
The same bash script that initiated the Python script now ensures the EC2 instance is shut down after the completion of all tasks.

## API Request Format
To create the backup using the Atlassian API, a GET request is sent to:


The base URL and progress URL are defined as:
```python
PRINCIPAL = 'financialtimes'
BASE_URL = f'https://{PRINCIPAL}.atlassian.net/wiki'
PROGRESS_URL = f'{BASE_URL}/rest/obm/1.0/getprogress.json'
