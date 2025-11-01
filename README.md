# Video Knowledge Convergence Project

## Project Overview

The "Video Knowledge Convergence" project is an intelligent system designed to extract and synthesize knowledge from YouTube videos. It automates the entire pipeline from video discovery to AI-powered content analysis and summarization. With user authentication, it provides a personalized experience for managing analysis templates and tracks usage.

## Features

- **Intelligent Video Search:** Finds relevant YouTube videos based on a user query.
- **Multi-source Transcription:** Prioritizes official subtitles and falls back to transcribing audio via Speech-to-Text.
- **AI-Powered Analysis:** Utilizes the Google Gemini AI model to analyze and summarize video transcripts.
- **User Authentication:** Secure user registration and login system using JWT (JSON Web Tokens).
- **Personal Template Management:** Logged-in users can create, view, update, and delete their own private analysis templates.
- **Rate Limiting:** Protects the service from abuse with usage limits:
  - **Anonymous Users:** 1 analysis per day (per IP).
  - **Authenticated Users:** 5 analyses per day.
- **Containerized Environment:** The entire application (backend and frontend) is containerized with Docker for easy setup and consistent deployment.

## Tech Stack

- **Backend:** Flask, Python, SQLAlchemy, Flask-Migrate
- **Frontend:** React, React Router, Axios
- **Database:** SQLite
- **Containerization:** Docker, Docker Compose
- **AI:** Google Gemini

## Getting Started

### Prerequisites

- Docker
- Docker Compose

### 1. Configuration

First, you need to set up your environment variables.

1.  Copy the example environment file:
    ```bash
    cp .env.example .env
    ```
2.  Open the newly created `.env` file in a text editor.
3.  Fill in the required API keys (`YOUTUBE_API_KEY`, `GEMINI_API_KEY`).
4.  Set a strong, random `SECRET_KEY` for signing authentication tokens. You can generate one with the following command:
    ```bash
    openssl rand -hex 32
    ```

### 2. Running the Application

With Docker running, execute the following command in the project root directory:

```bash
docker-compose up --build
```

This command will build the Docker images for both the frontend and backend services, install all dependencies, and start the application. The frontend will be available at `http://localhost:3000` and the backend at `http://localhost:5001`.

## Usage and Testing

### Manual Testing

Once the application is running, you can test the backend API endpoints using a tool like `curl`.

1.  **Register a new user:**
    ```bash
    curl -X POST -H "Content-Type: application/json" \
      -d '{"username": "testuser", "password": "password123"}' \
      http://localhost:5001/api/register
    ```

2.  **Log in to get a token:**
    ```bash
    curl -X POST -H "Content-Type: application/json" \
      -d '{"username": "testuser", "password": "password123"}' \
      http://localhost:5001/api/login
    ```
    This will return a JWT token. Copy it for the next step.

3.  **Access a protected route (e.g., get templates):**
    Replace `<your_token_here>` with the token you copied.
    ```bash
    curl -H "Authorization: Bearer <your_token_here>" http://localhost:5001/api/templates
    ```

### Automated Frontend Tests

The frontend project includes unit tests for the new authentication components.

1.  Ensure the Docker containers are running (`docker-compose up`).
2.  In a new terminal, execute the following command to run the tests:
    ```bash
    docker-compose exec frontend npm test
    ```

This will start the Jest test runner in watch mode inside the `frontend` container.