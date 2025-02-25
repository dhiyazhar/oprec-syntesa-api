import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import ORJSONResponse
from routes import submission

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

@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger = logging.getLogger("uvicorn.access")
    logger.info(f"Request: {request.method} {request.url}")
    response = await call_next(request)
    logger.info(f"Response status: {response.status_code}")
    return response

app.include_router(submission.router, prefix="/api")

@app.get("/")
async def root():
    return {"message": "Syntesa © 2025"}

@app.get("/health", response_class=ORJSONResponse)
async def health():
    return ORJSONResponse({"status": "ok"})