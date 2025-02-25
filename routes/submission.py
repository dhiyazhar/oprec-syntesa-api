import os
import asyncio
import logging
from io import BytesIO
from typing import Tuple, List
from datetime import datetime
from functools import lru_cache
from time import time
from dotenv import load_dotenv

from fastapi import APIRouter, File, Header, UploadFile, Form, Depends, HTTPException, status, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import ORJSONResponse
from pydantic import BaseModel, EmailStr, field_validator, constr
from google.oauth2.service_account import Credentials

from services.gsheets import GSheets
from services.gdrive import GDrive

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('registration.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

load_dotenv()

ALLOWED_FILE_TYPES = {'application/pdf'}
MAX_FILE_SIZE = 5 * 1024 * 1024
CREDENTIALS_PATH = 'env/google-key.json'

class UploadProgressTracker:
    def __init__(self, total_size: int, filename: str):
        self.total_size = total_size
        self.uploaded = 0
        self.filename = filename
        self.start_time = time()

    def update(self, chunk_size: int): 
        self.uploaded += chunk_size
        progress = self.uploaded / self.total_size * 100
        elapsed_time = time() - self.start_time
        speed = self.uploaded / elapsed_time if elapsed_time > 0 else 0

        logger.info(
            f'File: {self.filename} - Progress: {progress:.1f}% -'
            f'Speed: {speed/1024:.1f} KB/s'
        )

@lru_cache()
def get_credentials(scope: str) -> Credentials:
    logger.info(f'Loading credentials for scope: {scope}')
    try:
        return Credentials.from_service_account_file(
            CREDENTIALS_PATH,
            scopes=[scope]
        )
    except Exception as e:
        logger.error(f'Failed to load credentials: {str(e)}')
        raise

class FileValidator:
    @staticmethod
    async def validate_file(file: UploadFile) -> bytes:
        try: 
            content = await file.read()
            tracker = UploadProgressTracker(len(content), file.filename)

            if len(content) > MAX_FILE_SIZE:
                logger.warning(f'File size exceeded: {file.filename}')
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=f'File size exceeds {MAX_FILE_SIZE/1024/1024}MB limit'
                )
            
            if file.content_type not in ALLOWED_FILE_TYPES:
                logger.warning(f'Invalid file type: {file.content_type}')
                raise HTTPException(
                    status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                    detail=f'Only PDF files are allowed'
                )
            
            chunk_size = len(content) // 10
            for i in range(0, len(content), chunk_size):
                chunk = content[i:i + chunk_size]
                tracker.update(len(chunk))
                await asyncio.sleep(0.1)
            
            return content
        except Exception as e:
            logger.error(f'File validation error: {str(e)}')
            raise

class RegistrationData(BaseModel):
    nama: constr(min_length=2)
    email: EmailStr
    nim: constr(pattern=r'^\d{11}$')    
    prodi: constr(min_length=2)
    kelas: str

    @field_validator("nama")
    def validate_nama(cls, v: str) -> str:
        if any(char.isdigit() for char in v):
            raise ValueError("Nama tidak boleh mengandung angka")
        return v.title()

    @field_validator("email")
    def validate_email(cls, v: str) -> str:
        return v.lower()

    @field_validator("nim")
    def validate_nim(cls, v: str) -> str:
        if not v.isdigit():
            raise ValueError("NIM harus berupa angka")
        if len(v) != 11:
            raise ValueError("NIM harus tepat 11 digit")
        return v

    @field_validator("prodi")
    def validate_prodi(cls, v: str) -> str:
        return v.title()

    @field_validator("kelas")
    def validate_kelas(cls, v: str) -> str:
        return v.upper()

class GoogleServices: 
    def __init__(self):
        self.drive_scope = 'https://www.googleapis.com/auth/drive'
        self.sheets_scope = 'https://www.googleapis.com/auth/spreadsheets'
        logger.info('Initializing Google Services')
    
    @property
    def drive(self) -> GDrive:
        return GDrive(get_credentials(self.drive_scope))
    
    @property
    def sheets(self) -> GSheets:
        return GSheets(get_credentials(self.sheets_scope))
    
services = GoogleServices()

def verify_api_key(x_api_key: str = Header(...)):
    api_key = os.getenv("API_KEY")
    if not api_key:
        logger.warning("Invalid API key attempt")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Invalid API key'
        )
    return x_api_key

def generate_filename(nim: str, nama: str, kelas: str, file_type: str) -> str:
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    return f"{nim}_{nama.replace(' ', '')}_{kelas}_{file_type}_{timestamp}.pdf"

async def upload_files(
    gdrive: GDrive,
    files_data: List[Tuple[bytes, str]]
) -> List[str]:
    logger.info(f'Starting upload of {len(files_data)} files')
    upload_start_time = time()
    
    upload_tasks = [
        gdrive.upload_file(content, filename)
        for content, filename in files_data
    ]
    
    results = await asyncio.gather(*upload_tasks, return_exceptions=True)
    
    failed_uploads = [i for i, result in enumerate(results) if isinstance(result, Exception)]
    if failed_uploads:
        logger.error(f'Upload failed for files at indices: {failed_uploads}')
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f'Failed to upload files at indices {failed_uploads}'
        )
    
    upload_duration = time() - upload_start_time
    logger.info(f'Upload completed in {upload_duration:.2f} seconds')
    
    return results
      
router = APIRouter()

@router.post("/register", status_code=status.HTTP_201_CREATED, response_class=ORJSONResponse)
async def register(
    request: Request,
    x_api_key: str = Depends(verify_api_key),
    nama: str = Form(...),
    email: str = Form(...),
    nim: str = Form(...),
    prodi: str = Form(...),
    kelas: str = Form(...),
    cv: UploadFile = File(...),
    transcript: UploadFile = File(...),
):
    registration_start_time = time()
    logger.info(f'Starting registration process for NIM: {nim}')
    try:
        reg_data = RegistrationData(
            nama=nama, 
            email=email,
            nim=nim, 
            prodi=prodi,
            kelas=kelas
        )
        logger.info(f'Registration data validated for {reg_data.nim}')
        
        logger.info(f'Starting file validation')
        cv_content, transcript_content = await asyncio.gather(
            FileValidator.validate_file(cv),
            FileValidator.validate_file(transcript)
        )
        logger.info('File validation completed.')
        
        cv_name = generate_filename(nim, reg_data.nama, kelas, 'cv')
        transcript_name = generate_filename(nim, reg_data.nama, kelas, 'transcript')
        
        logger.info('Starting file upload to Google Drive')
        cv_link, transcript_link = await upload_files(
            services.drive,
            [(cv_content, cv_name), (transcript_content, transcript_name)]
        )
        
        logger.info('Updating registration data in Google Sheets')
        data = [[reg_data.nama, reg_data.email, reg_data.nim, reg_data.prodi, reg_data.kelas, cv_link, transcript_link]]
        
        if not await services.sheets.append_data(data):
            logger.error('Failed to upload Google Sheets.')
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail='Failed to update registration form.'
            )

        registration_duration = time() - registration_start_time
        logger.info(
            f'Registration completed for NIM: {reg_data.nama} '
            f'(NIM: {reg_data.nim}) in {registration_duration:.2f} seconds'
        )
        
        return {
            "message": "Registration succesful"
        }        
        
    except ValueError as e:
        logger.error(f'Validation error for NIM {nim}: {str(e)}')
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f'Unexpected error during registration: {str(e)}')
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'An unexpected error occured: {str(e)}'
        )
        