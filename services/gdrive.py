from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from io import BytesIO

class GDrive:
    def __init__(self, credentials):
        self.service = build('drive', 'v3', credentials=credentials)

    def upload_file(self, content: bytes, name: str, folder_id='1smQZF4yvQsx7fuFYTlG0uN2GX9lRYIlR'):
        file_metadata = {'name': name, 'parents': [folder_id]}
        media = MediaIoBaseUpload(BytesIO(content), mimetype='application/pdf')
        try:
            file = self.service.files().create(body=file_metadata, media_body=media, fields='id').execute()
            self.service.permissions().create(fileId=file['id'], body={'type': 'anyone', 'role': 'reader'}).execute()
            return f"https://drive.google.com/file/d/{file['id']}/view"
        except Exception as e:
            print(f"Drive upload error: {e}")
            return None