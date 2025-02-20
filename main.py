from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import ORJSONResponse

app = FastAPI(
    title="API Registrasi",
    version="1.0",
    default_response_class=ORJSONResponse
)

app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from routes import submission
app.include_router(submission.router, prefix="/api")

@app.get("/")
async def root():
    return {"message": "Syntesa © 2025"}