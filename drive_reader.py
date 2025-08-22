import os
import streamlit as st
from googleapiclient.discovery import build
from google.oauth2 import service_account

# 📌 REQUIRED CONFIG
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
FOLDER_NAME = 'AI_CEO_KnowledgeBase'  # Top-level folder name in your Google Drive

# ✅ Load credentials from Streamlit Secrets [gdrive]
gdrive_secrets = st.secrets["gdrive"]
creds = service_account.Credentials.from_service_account_info(
    dict(gdrive_secrets), scopes=SCOPES
)

# Build the Google Drive service
service = build('drive', 'v3', credentials=creds)

def get_folder_id(service, folder_name):
    """Return the folder ID for a given folder name."""
    query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder'"
    response = service.files().list(q=query, spaces='drive', fields='files(id, name)').execute()

    folders = response.get('files', [])
    if not folders:
        st.error(f"❌ Folder '{folder_name}' not found.")
        return None
    return folders[0]['id']

def list_files_in_folder(service, folder_id):
    """List all files inside the folder ID."""
    results = service.files().list(
        q=f"'{folder_id}' in parents",
        fields="files(id, name, mimeType, modifiedTime)",
        pageSize=1000
    ).execute()

    files = results.get('files', [])
    if not files:
        st.warning("⚠️ No files found in the folder.")
        return

    st.markdown("### 📂 Files Found:")
    for f in files:
        st.markdown(f"- 📄 `{f['name']}` | `{f['mimeType']}` | Modified: `{f['modifiedTime']}`")

def main():
    st.title("📁 Google Drive File Viewer")
    folder_id = get_folder_id(service, FOLDER_NAME)

    if folder_id:
        list_files_in_folder(service, folder_id)

if __name__ == '__main__':
    main()
