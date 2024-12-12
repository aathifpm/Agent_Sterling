import sys
import os
from pathlib import Path
import logging
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
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

try:
    # Import the main application routes
    from src.app import app as main_app
    for route in main_app.routes:
        app.routes.append(route)
except Exception as e:
    logger.error(f"Error importing main app: {str(e)}")
    # Continue running even if main app import fails
    pass

@app.exception_handler(404)
async def custom_404_handler(request, exc):
    if request.url.path.startswith("/static/"):
        return JSONResponse(
            status_code=404,
            content={"message": f"File not found: {request.url.path}"}
        )
    return FileResponse('static/index.html')

# Serve index.html for the root path
@app.get("/")
async def read_root():
    return FileResponse('static/index.html')

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

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": str(datetime.now())} 