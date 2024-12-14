import sys
import os
from pathlib import Path
import logging
from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('bot.log')
    ]
)
logger = logging.getLogger(__name__)

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# Create the FastAPI application
app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files with custom configuration
app.mount("/static", StaticFiles(directory="static", html=True), name="static")

# Error handlers
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    if request.url.path.startswith("/api/"):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": str(exc.detail)}
        )
    if exc.status_code == 404:
        return FileResponse('static/index.html')
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": str(exc.detail)}
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"General error: {str(exc)}", exc_info=True)
    if request.url.path.startswith("/api/"):
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"}
        )
    return FileResponse('static/index.html')

try:
    # Import the main application routes
    from src.app import app as main_app
    for route in main_app.routes:
        app.routes.append(route)
except Exception as e:
    logger.error(f"Error importing main app: {str(e)}")
    # Continue running even if main app import fails
    pass

# Serve index.html for the root path
@app.get("/")
async def read_root():
    return FileResponse('static/dashboard.html')

# API health check endpoint
@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "timestamp": str(datetime.now())}

# Serve static files directly
@app.get("/styles.css")
async def get_css():
    return FileResponse('static/styles.css', media_type='text/css')

@app.get("/app.js")
async def get_js():
    return FileResponse('static/app.js', media_type='application/javascript')

@app.get("/sterling.jpg")
async def get_image():
    return FileResponse('static/sterling.jpg', media_type='image/jpeg') 