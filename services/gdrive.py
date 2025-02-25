import logging
from typing import Optional, Dict, Any
from io import BytesIO
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from googleapiclient.errors import HttpError
from google.oauth2.service_account import Credentials
from tenacity import retry, stop_after_attempt, wait_exponential
from fastapi.concurrency import run_in_threadpool

logger = logging.getLogger(__name__)

class GDriveException(Exception):
    pass

class GDrive:
    def __init__(self, credentials: Credentials, default_folder_id: str = '1smQZF4yvQsx7fuFYTlG0uN2GX9lRYIlR'):
        self.credentials = credentials
        self.default_folder_id = default_folder_id
        logger.info('GDrive service initiated.')

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        reraise=True
    )
    async def upload_file(self, content: bytes, name: str, folder_id: Optional[str] = None, mime_type: str = 'application/pdf') -> Optional[str]:
        try:
            service = build('drive', 'v3', credentials=self.credentials, cache_discovery=False)
            
            file_metadata: Dict[str, Any] = {
                'name': name,
                'parents': [folder_id or self.default_folder_id]
            }
            
            media = MediaIoBaseUpload(
                BytesIO(content),
                mimetype=mime_type,
                resumable=False
            )
            
            logger.info(f"Starting to upload file: {name}")
            file = await run_in_threadpool(
                lambda: service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id'
            ).execute())
            
            logger.info(f"File uploaded successfully. ID: {file['id']}")
            
            await run_in_threadpool(lambda: service.permissions().create(
                fileId=file['id'],
                body={'type': 'anyone', 'role': 'reader'},
                fields='id'
            ).execute())
            
            logger.info(f"Public permission set for file: {file['id']}")
            return f"https://drive.google.com/file/d/{file['id']}/view"
        
        except HttpError as e:
            error_msg = f"Google Drive API error: {str(e)}"
            logger.error(error_msg)
            raise GDriveException(error_msg)
        except Exception as e:
            error_msg = f"Unexpected error during upload: {str(e)}"
            logger.error(error_msg)
            raise GDriveException(error_msg)
