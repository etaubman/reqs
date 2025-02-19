# ======================================
# Module: API Server for Generative AI Feature Requests
# This module initializes environment variables, database, AI models, and defines API endpoints.
# ======================================

# Import necessary modules for database, security, date/time, JSON and API functionality.
import sqlite3
import hashlib
import datetime
import json
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv
import google.generativeai as genai

# ======================================
# Load Environment Variables
# ======================================
load_dotenv()  # Load variables from .env file into environment

gemini_api_key = os.getenv("GEMINI_API_KEY")
if not gemini_api_key:
    # Terminate if critical API key is not provided
    raise Exception("GEMINI_API_KEY not set in environment")
# Configure generative AI with the API key
genai.configure(api_key=gemini_api_key)

# ======================================
# Setup SQLite Database
# ======================================
# Determine current file directory to locate or create the database file.
base_dir = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(base_dir, "feature_requests.db")
# Connect with SQLite ensuring thread-safety
db_conn = sqlite3.connect(db_path, check_same_thread=False)
cursor = db_conn.cursor()
# Create the feature_requests table if it doesn't exist
cursor.execute("""
    CREATE TABLE IF NOT EXISTS feature_requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        feature_text TEXT,
        submission_time DATETIME,
        ip TEXT,
        json_response TEXT,
        response_md5 TEXT,
        epic_title TEXT
    )
""")
db_conn.commit()

# ======================================
# Read Prompt Files
# ======================================
# Load main system prompt for feature generation.
prompt_file = os.path.join(base_dir, "prompts", "feature_main_system_prompt.txt")
with open(prompt_file, "r", encoding="utf-8") as f:
    system_prompt = f.read()

# Load ideas system prompt to guide message ideas generation.
ideas_prompt_file = os.path.join(base_dir, "prompts", "ideas_system_prompt.txt")
with open(ideas_prompt_file, "r", encoding="utf-8") as f:
    ideas_prompt = f.read()

# ======================================
# Define Generation Configurations for AI Models
# ======================================
feature_generation_config = {
    "temperature": .7,
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 8192,
    "response_mime_type": "application/json",
}
ideas_generation_config = {
    "temperature": 0.6,
    "top_p": 0.9,
    "top_k": 50,
    "max_output_tokens": 4096,
    "response_mime_type": "application/json",
}

# ======================================
# Initialize Generative AI Models
# ======================================
# Model for feature generation using the system prompt.
model = genai.GenerativeModel(
    model_name="gemini-2.0-flash",
    generation_config=feature_generation_config,
    system_instruction=system_prompt,
)
# Model for ideas generation using the ideas prompt.
ideas_model = genai.GenerativeModel(
    model_name="gemini-2.0-flash",
    generation_config=ideas_generation_config,
    system_instruction=ideas_prompt,
)

# ======================================
# Initialize the FastAPI Application
# ======================================
app = FastAPI()

# ======================================
# Middleware for Logging Requests and Responses
# ======================================
@app.middleware("http")
async def log_requests(request: Request, call_next):
    # Log every incoming request with method and URL.
    print("DEBUG: Received request:", request.method, request.url, flush=True)
    response = await call_next(request)
    # Log the response status code after processing the request.
    print("DEBUG: Response status code:", response.status_code, flush=True)
    return response

# ======================================
# CORS Middleware Setup
# ======================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this to your actual frontend domain.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ======================================
# Static File Setup
# ======================================
# Calculate absolute paths to enable serving static files.
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_static = os.path.join(os.path.dirname(current_dir), "static")
if os.path.exists(parent_static) and os.path.isdir(parent_static):
    static_dir = parent_static  # Prefer sibling static folder during local development.
else:
    static_dir = os.path.join(current_dir, "static")  # Use local static folder for containerized deployment.
index_path = os.path.join(static_dir, "index.html")

# Create static directory if it does not exist to avoid runtime errors.
if not os.path.exists(static_dir):
    os.makedirs(static_dir)

print(f"Static directory: {static_dir}", flush=True)  # Debug print: verify static directory path.
print(f"Index path: {index_path}", flush=True)         # Debug print: verify index file path.

# ======================================
# API Routes
# ======================================

# Endpoint: Generate a feature based on description
@app.post("/api/generate")
async def generate_feature(request: Request):
    """
    Generate a feature based on the provided description.
    Expects a JSON payload with "description" and returns the generated feature as JSON.
    """
    # Receive JSON data from the client.
    data = await request.json()
    feature_description = data.get("description")
    print("DEBUG: Received /api/generate request with description:", feature_description, flush=True)
    if not feature_description:
        # Return error if description is missing.
        return JSONResponse(status_code=400, content={"error": "Missing feature description"})
    try:
        # Create a session for interacting with the generative model.
        chat_session = genai.ChatSession(model=model)
        # Use the chat session to generate a response from the AI.
        response = chat_session.send_message(feature_description)
        result_text = response.text if hasattr(response, "text") else str(response)
        # Extract epic title from JSON response if available.
        try:
            response_json = json.loads(result_text)
            epic_title = response_json.get("epic_title", "")
        except Exception:
            epic_title = ""
        # Compute MD5 hash of the response for unique identification.
        response_md5 = hashlib.md5(result_text.encode("utf-8")).hexdigest()
        submission_time = datetime.datetime.now().isoformat()
        ip = request.client.host if request.client and request.client.host else ""
        # Save the generated feature data into the SQLite database.
        cursor.execute("""
            INSERT INTO feature_requests (feature_text, submission_time, ip, json_response, response_md5, epic_title)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (feature_description, submission_time, ip, result_text, response_md5, epic_title))
        db_conn.commit()
        print("DEBUG: Generation result:", result_text, flush=True)
        return JSONResponse(content={"result": result_text})
    except Exception as e:
        print(f"DEBUG: Error generating feature: {str(e)}", flush=True)
        return JSONResponse(status_code=500, content={"error": str(e)})

# Endpoint: Generate ideas with an optional focus parameter for additional context.
@app.get("/api/generate-ideas")
async def generate_ideas(focus: str = None):
    """
    Generate ideas using an optional focus parameter.
    Accepts an optional "focus" query parameter and returns generated ideas in JSON format.
    """
    try:
        chat_session = genai.ChatSession(model=ideas_model)
        # Provide a default focus if none is supplied.
        if focus is None:
            focus = "none"
        message = f"focus: {focus}"
        print("DEBUG: Generating ideas with focus:", focus, flush=True)
        print("DEBUG: Message:", message, flush=True)
        response = chat_session.send_message(message)
        result_text = response.text if hasattr(response, "text") else str(response)
        return JSONResponse(content={"result": result_text})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

# Endpoint: Serve a preloaded page based on the MD5 hash of the feature request
@app.get("/generated/{md5_hash}")
async def get_generated(md5_hash: str):
    """
    Retrieve a generated feature page by MD5 hash.
    Looks up the feature request in the database and injects preloaded data into HTML.
    """
    # Lookup feature request in the database using its MD5 hash.
    record = cursor.execute(
        "SELECT json_response FROM feature_requests WHERE response_md5 = ?",
        (md5_hash,)
    ).fetchone()
    if not record:
        return JSONResponse(status_code=404, content={"error": "Feature request not found"})
    json_response = record[0]
    try:
        data = json.loads(json_response)
    except Exception:
        data = {}
    # Read the contents of the index.html file.
    try:
        with open(index_path, "r", encoding="utf-8") as f:
            html_content = f.read()
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": "Index file not found"})
    # Inject the preloaded feature data into the HTML before closing the body tag.
    preload_script = f'<script>window.preloadedFeatureData = {json.dumps(data)};</script>'
    modified_html = html_content.replace("</body>", preload_script + "\n</body>")
    return HTMLResponse(content=modified_html, status_code=200)

# Endpoint: Return all feature requests in descending order of submission time.
@app.get("/api/feature-requests")
async def get_feature_requests():
    """
    Retrieve all submitted feature requests.
    Returns a list of feature requests in descending order by submission time.
    """
    cursor.execute("""
        SELECT submission_time, epic_title, response_md5 
        FROM feature_requests 
        ORDER BY submission_time DESC
    """)
    rows = cursor.fetchall()
    requests_list = []
    for row in rows:
        requests_list.append({
            "submission_time": row[0],
            "epic_title": row[1],
            "response_md5": row[2]
        })
    return JSONResponse(content=requests_list)

# Health check endpoint to verify server status.
@app.get("/api/health")
async def healthcheck():
    """
    Check server health.
    Returns a JSON response indicating the server is healthy.
    """
    return JSONResponse(content={"status": "healthy"}, status_code=200)

# Simple test endpoint to validate the server is running.
@app.get("/ping")
async def ping():
    """
    Return a simple pong message.
    Used to verify that the server is running.
    """
    return JSONResponse(content={"message": "pong"})

# Root endpoint: Serve the index.html file for the web interface.
@app.get("/")
async def read_root():
    """
    Serve the main index.html page.
    Returns index.html if found; otherwise, a 404 error is returned.
    """
    if os.path.exists(index_path):
        print(f"Serving index.html from: {index_path}", flush=True)
        return FileResponse(index_path)
    else:
        print(f"Index file not found at: {index_path}", flush=True)
        return JSONResponse(status_code=404, content={"error": "Index file not found"})

# Endpoint: Serve the generated.html page from the static folder.
@app.get("/generated", response_class=FileResponse)
async def serve_generated_page():
    """
    Serve the generated.html page from the static folder.
    Returns the generated page file if available, or an error if not found.
    """
    generated_page_path = os.path.join(static_dir, "generated.html")
    if os.path.exists(generated_page_path):
        return FileResponse(generated_page_path)
    else:
        return JSONResponse(status_code=404, content={"error": "Generated page not found"})

# Mount the static directory to serve static assets such as JavaScript, CSS, and images.
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# ======================================
# Application Startup Code
# ======================================
if __name__ == "__main__":
    import uvicorn
    # Debug: List all registered routes for verification.
    print("Available routes:", flush=True)
    for route in app.routes:
        try:
            print(route.path, flush=True)
        except Exception:
            pass
    # Run the FastAPI application with automatic reload enabled.
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
