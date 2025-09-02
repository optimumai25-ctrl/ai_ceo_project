# ------------------------------
# 📁 drive_reader.py
# ------------------------------
import os
import io
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from google.oauth2 import service_account
import docx
import pandas as pd
from PyPDF2 import PdfReader


FOLDER_NAME = 'AI_CEO_KnowledgeBase'
OUTPUT_DIR = 'parsed_data'
os.makedirs(OUTPUT_DIR, exist_ok=True)

SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]
creds = service_account.Credentials.from_service_account_file("gdrive_credentials.json", scopes=SCOPES)
service = build("drive", "v3", credentials=creds)


def get_folder_id(folder_name):
    query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder'"
    results = service.files().list(q=query, spaces='drive', fields='files(id, name)').execute()
    folders = results.get('files', [])
    if not folders:
        raise Exception(f"Folder '{folder_name}' not found in Drive.")
    return folders[0]['id']


def list_folder_contents(parent_id):
    query = f"'{parent_id}' in parents"
    results = service.files().list(q=query, fields='files(id, name, mimeType)').execute()
    return results.get('files', [])


def download_file(file_id):
    request = service.files().get_media(fileId=file_id)
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while not done:
        _, done = downloader.next_chunk()
    fh.seek(0)
    return fh


def extract_text_from_pdf(fh):
    reader = PdfReader(fh)
    return "\n".join([page.extract_text() or "" for page in reader.pages])


def extract_text_from_docx(fh):
    doc = docx.Document(fh)
    return "\n".join(p.text for p in doc.paragraphs)


def export_google_file(file_id, mime_target):
    request = service.files().export_media(fileId=file_id, mimeType=mime_target)
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while not done:
        _, done = downloader.next_chunk()
    fh.seek(0)
    return fh.getvalue()


def save_text(name_no_ext, text):
    safe = "".join(c for c in name_no_ext if c.isalnum() or c in (" ", "-", "_")).rstrip()
    out_path = os.path.join(OUTPUT_DIR, f"{safe}.txt")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(text)
    return out_path


def main():
    folder_id = get_folder_id(FOLDER_NAME)
    files = list_folder_contents(folder_id)

    for f in files:
        fid = f["id"]
        fname = f["name"]
        mime = f.get("mimeType", "")

        try:
            if mime == "application/pdf":
                fh = download_file(fid)
                text = extract_text_from_pdf(fh)
                save_text(os.path.splitext(fname)[0], text)

            elif mime == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                fh = download_file(fid)
                text = extract_text_from_docx(fh)
                save_text(os.path.splitext(fname)[0], text)

            elif mime == "text/plain":
                fh = download_file(fid)
                text = fh.read().decode("utf-8", errors="ignore")
                save_text(os.path.splitext(fname)[0], text)

            # Google Docs → export as plain text
            elif mime == "application/vnd.google-apps.document":
                data = export_google_file(fid, "text/plain")
                text = data.decode("utf-8", errors="ignore")
                save_text(fname, text)

            # Google Sheets → export as CSV and stringify
            elif mime == "application/vnd.google-apps.spreadsheet":
                data = export_google_file(fid, "text/csv")
                df = pd.read_csv(io.BytesIO(data))
                text = df.to_csv(index=False)
                save_text(fname, text)

            # Unsupported types are skipped gracefully
            else:
                # You could add more handlers (Slides, etc.) if needed
                continue

        except Exception as e:
            # Log and continue with other files
            print(f"Failed to parse '{fname}': {e}")


if __name__ == "__main__":
    main()
