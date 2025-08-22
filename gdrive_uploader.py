import os
import streamlit as st
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2 import service_account

# --------------------------------------------
# 🔐 Use service account from Streamlit secrets
# --------------------------------------------
SCOPES = ["https://www.googleapis.com/auth/drive"]
gdrive_secrets = st.secrets["gdrive"]  # stored in .streamlit/secrets.toml
SHARED_DRIVE_ID = st.secrets["shared_drive_id"]  # also stored in secrets

# Authenticate using Streamlit secrets
token_info = dict(gdrive_secrets)
creds = service_account.Credentials.from_service_account_info(token_info, scopes=SCOPES)
service = build("drive", "v3", credentials=creds)

# --------------------------------------------
# 📁 Find or create folder in Shared Drive
# --------------------------------------------
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

# --------------------------------------------
# ⬆️ Upload or update file to folder
# --------------------------------------------
def upload_or_update_file(service, file_path, folder_id):
    file_name = os.path.basename(file_path)

    query = (
        f"name='{file_name}' and '{folder_id}' in parents and trashed = false"
    )

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
        file_id = files[0]['id']
        service.files().update(
            fileId=file_id,
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
