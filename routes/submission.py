import os
from io import BytesIO
from dotenv import load_dotenv
from fastapi import APIRouter, File, UploadFile, Form, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from google.oauth2.service_account import Credentials
from fastapi.concurrency import run_in_threadpool
from services.gsheets import GSheets
from services.gdrive import GDrive

router = APIRouter()

load_dotenv()
API_KEY = os.getenv("API_KEY")
CREDENTIALS_PATH = './env/google-key.json'

drive_creds = Credentials.from_service_account_file(
    CREDENTIALS_PATH, scopes=['https://www.googleapis.com/auth/drive']
)
sheets_creds = Credentials.from_service_account_file(
    CREDENTIALS_PATH, scopes=['https://www.googleapis.com/auth/spreadsheets']
)

def get_gdrive():
    return GDrive(drive_creds)

def get_gsheets():
    return GSheets(sheets_creds)

def verify_api_key(x_api_key: str = Form(...)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API Key")
    return x_api_key

class RegistrationData(BaseModel):
    nama: str
    email: EmailStr
    nim: str
    prodi: str
    kelas: str

def generate_filename(nim: str, nama: str, kelas: str, file_type: str) -> str:
    return f"{nim}_{nama.replace(' ', '')}_{kelas}_{file_type}.pdf"

@router.post("/register", status_code=201, response_class=ORJSONResponse)
async def register(
    x_api_key: str = Depends(verify_api_key),
    nama: str = Form(...),
    email: str = Form(...),
    nim: str = Form(...),
    prodi: str = Form(...),
    kelas: str = Form(...),
    cv: UploadFile = File(...),
    transcript: UploadFile = File(...),
    gdrive: GDrive = Depends(get_gdrive),
    gsheets: GSheets = Depends(get_gsheets),
):
    try:
        RegistrationData(nama=nama, email=email, nim=nim, prodi=prodi, kelas=kelas)
    except Exception as e:
        raise HTTPException(400, detail="Invalid data")

    cv_content = await cv.read()
    transcript_content = await transcript.read()

    cv_name = generate_filename(nim, nama, kelas, "cv")
    transcript_name = generate_filename(nim, nama, kelas, "transcript")

    cv_link, transcript_link = await asyncio.gather(
        run_in_threadpool(gdrive.upload_file, cv_content, cv_name),
        run_in_threadpool(gdrive.upload_file, transcript_content, transcript_name)
    )

    if not (cv_link and transcript_link):
        raise HTTPException(500, detail="File upload failed")

    data = [[nama, email, nim, prodi, kelas, cv_link, transcript_link]]
    if not await run_in_threadpool(gsheets.append_data, data):
        raise HTTPException(500, detail="Sheets update failed")

    return {"message": "Success", "cv_link": cv_link, "transcript_link": transcript_link}