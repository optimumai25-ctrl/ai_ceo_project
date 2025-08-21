import io
import streamlit as st
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2 import service_account
import json

# Setup from Streamlit secrets
SCOPES = ["https://www.googleapis.com/auth/drive"]
gdrive_secrets = st.secrets["gdrive"]

creds = service_account.Credentials.from_service_account_info(
    dict(gdrive_secrets), scopes=SCOPES
)
service = build("drive", "v3", credentials=creds)

def authenticate_drive():
    return service

def find_or_create_folder(service, folder_name, parent_id=None):
    query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder'"
    if parent_id:
        query += f" and '{parent_id}' in parents"

    results = service.files().list(q=query, spaces='drive', fields='files(id, name)').execute()
    folders = results.get('files', [])

    if folders:
        return folders[0]['id']

    file_metadata = {
        'name': folder_name,
        'mimeType': 'application/vnd.google-apps.folder'
    }
    if parent_id:
        file_metadata['parents'] = [parent_id]

    folder = service.files().create(body=file_metadata, fields='id').execute()
    return folder.get('id')

def upload_or_update_file(service, file_path, folder_id):
    file_name = file_path.split("/")[-1]

    # Check if file already exists
    query = f"name='{file_name}' and '{folder_id}' in parents"
    results = service.files().list(q=query, spaces='drive', fields='files(id, name)').execute()
    files = results.get('files', [])

    media = MediaFileUpload(file_path, resumable=True)

    if files:
        # Update existing file
        file_id = files[0]['id']
        service.files().update(fileId=file_id, media_body=media).execute()
    else:
        # Upload new file
        file_metadata = {'name': file_name, 'parents': [folder_id]}
        service.files().create(body=file_metadata, media_body=media, fields='id').execute()
