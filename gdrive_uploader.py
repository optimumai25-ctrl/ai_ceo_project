import os
import streamlit as st
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2 import service_account

SCOPES = ["https://www.googleapis.com/auth/drive"]
gdrive_secrets = st.secrets["gdrive"]
SHARED_DRIVE_ID = gdrive_secrets["shared_drive_id"]

creds = service_account.Credentials.from_service_account_info(
    dict(gdrive_secrets), scopes=SCOPES
)
service = build("drive", "v3", credentials=creds)

def find_or_create_folder(service, folder_name, parent_id):
    query = (
        f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' "
        f"and '{parent_id}' in parents and trashed = false"
    )
    results = service.files().list(
        q=query,
        spaces='drive',
        fields='files(id, name)',
        supportsAllDrives=True,
        includeItemsFromAllDrives=True
    ).execute()
    folders = results.get('files', [])
    if folders:
        return folders[0]['id']

    metadata = {
        'name': folder_name,
        'mimeType': 'application/vnd.google-apps.folder',
        'parents': [parent_id]
    }
    folder = service.files().create(
        body=metadata,
        fields='id',
        supportsAllDrives=True
    ).execute()
    return folder.get('id')

def upload_or_update_file(service, file_path, folder_id):
    file_name = os.path.basename(file_path)
    query = f"name='{file_name}' and '{folder_id}' in parents and trashed = false"
    results = service.files().list(
        q=query,
        spaces='drive',
        fields='files(id, name)',
        supportsAllDrives=True,
        includeItemsFromAllDrives=True
    ).execute()
    files = results.get('files', [])
    media = MediaFileUpload(file_path, resumable=True)

    if files:
        service.files().update(
            fileId=files[0]['id'],
            media_body=media,
            supportsAllDrives=True
        ).execute()
        print(f"✅ Updated file: {file_name}")
    else:
        metadata = {
            'name': file_name,
            'parents': [folder_id]
        }
        service.files().create(
            body=metadata,
            media_body=media,
            fields='id',
            supportsAllDrives=True
        ).execute()
        print(f"✅ Uploaded file: {file_name}")
