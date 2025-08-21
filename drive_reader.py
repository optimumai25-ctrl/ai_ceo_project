import os
import pickle
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow

# 📌 REQUIRED CONFIG
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
FOLDER_NAME = 'AI_CEO_KnowledgeBase'  # Main folder name in your Google Drive

def authenticate_google_drive():
    """Authenticate and return Drive API service."""
    creds = None
    token_path = 'token.pickle'
    creds_path = 'credentials/credentials.json'

    # Load token if exists
    if os.path.exists(token_path):
        with open(token_path, 'rb') as token:
            creds = pickle.load(token)

    # If no token or expired
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(creds_path, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(token_path, 'wb') as token:
            pickle.dump(creds, token)

    return build('drive', 'v3', credentials=creds)

def get_folder_id(service, folder_name):
    """Return the folder ID for a given folder name."""
    response = service.files().list(
        q=f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder'",
        spaces='drive',
        fields='files(id, name)',
    ).execute()

    folders = response.get('files', [])
    if not folders:
        print(f"❌ Folder '{folder_name}' not found.")
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
        print("⚠️ No files found in the folder.")
        return

    print("\n📂 Files found:")
    for f in files:
        print(f"📄 {f['name']} | {f['mimeType']} | Modified: {f['modifiedTime']}")

def main():
    service = authenticate_google_drive()
    folder_id = get_folder_id(service, FOLDER_NAME)

    if folder_id:
        list_files_in_folder(service, folder_id)

if __name__ == '__main__':
    main()
