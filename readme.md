# Epic Brainstorm Application

## Overview
This application is a brainstorming tool that generates epics and user stories for workflow platform features. It uses FastAPI for the backend with a generative AI API to create feature ideas and detailed responses. The application serves a main page for submitting ideas and a page to view previously generated responses.

## Getting Started Locally

### Prerequisites
- Install [Python 3.10+](https://www.python.org/)
- Docker (optional, for containerized deployment)
- Git

### Setup Instructions

1. **Clone the Repository**  
   Navigate to your preferred project directory and clone the repository:
   ```
   git clone <repository-url> <project-directory>
   ```

2. **Create and Activate Virtual Environment**  
   Change directory to the api folder:
   ```
   cd <project-directory>/api
   ```
   Create a virtual environment:
   ```
   python -m venv venv
   ```
   Activate the virtual environment:
   - On Windows:
     ```
     venv\Scripts\activate
     ```
   - On Linux/Mac:
     ```
     source venv/bin/activate
     ```

3. **Install Dependencies**  
   ```
   pip install -r requirements.txt
   ```

4. **Configure Environment**  
   Create a `.env` file in the `api` folder with at least the following entry:
   ```
   GEMINI_API_KEY=your_api_key_here
   ```

5. **Run the Application**  
   - **Directly with Python:**  
     From the `api` directory run:
     ```
     uvicorn api:app --reload --host 0.0.0.0 --port 8000
     ```
   - **Using Docker Compose:**  
     From the project root run:
     ```
     docker-compose up --build
     ```

6. **Access the App**  
   Open a browser and navigate to:
   - Main interface: `http://localhost:4200`
   - To view generated responses, click the "View Generated Responses" link on the main page.

## File Descriptions

- **docker-compose.yml**  
  Defines the containerized service for the API, including build context, environment variables, and networks.

- **api/static/style.css**  
  Contains all CSS styles for the application including layout, colors, and component styling.

- **api/static/script.js**  
  Implements the client-side functionality such as handling form submissions, fetching generated data, and dynamically rendering responses.

- **api/static/index.html**  
  Main entry point for the web interface. Contains the input form and placeholders for generated content.

- **api/static/generated.html**  
  Provides a page that displays a list of recent generated responses with links to detailed views.

- **api/requirements.txt**  
  Lists all Python dependencies required by the FastAPI backend.

- **api/prompts/ideas_system_prompt.txt**  
  Contains the instructions for generating random feature ideas based on an optional focus.

- **api/prompts/feature_main_system_prompt.txt**  
  Defines the prompt structure for generating detailed epics and stories based on a user-provided description.

- **api/Dockerfile**  
  Specifies the Docker build steps: setting the working directory, installing dependencies, copying source code, and launching the application with Uvicorn.

- **api/api.py**  
  Main FastAPI application file that sets up API endpoints for generating features and ideas, serving static content, handling database storage, and more.

- **.gitignore**  
  Lists files and folders to be excluded from version control (e.g., virtual environment, cache directories, and the SQLite database file).

## Summary
This project provides a generative AI-based solution for creating product features. It consists of a FastAPI backend that uses Docker for deployment, a SQLite database for storing generated responses, and a simple dynamic frontend built using plain HTML, CSS, and JavaScript.
