# Python Backend for Agentic App Platform

This is the Python backend using FastAPI and the E2B Python SDK.

## Setup

### 1. Create virtual environment

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Set up environment variables

```bash
cp .env.example .env
# Edit .env and add your API keys
```

### 4. Run the server

```bash
python main.py
# Or with uvicorn directly:
uvicorn main:app --reload --port 8000
```

The server will start at `http://localhost:8000`

## API Endpoints

### `GET /`
Health check endpoint.

### `POST /api/chat`
Generate code using LLM with streaming response.

**Request body:**
```json
{
  "messages": [...],
  "userID": "optional-user-id",
  "teamID": "optional-team-id",
  "template": {...},
  "model": {
    "id": "claude-sonnet-4-20250514",
    "name": "Claude Sonnet 4",
    "provider": "Anthropic",
    "providerId": "anthropic"
  },
  "config": {
    "apiKey": "optional-override-key",
    "temperature": 0.7
  }
}
```

### `POST /api/sandbox`
Create and run a sandbox with the generated code.

**Request body:**
```json
{
  "fragment": {
    "template": "code-interpreter-v1",
    "code": "print('Hello, World!')",
    "file_path": "script.py",
    ...
  },
  "userID": "optional-user-id",
  "teamID": "optional-team-id"
}
```

### `POST /api/morph-chat`
Edit existing code using LLM with Morph-style edits.

**Request body:**
```json
{
  "messages": [...],
  "model": {...},
  "config": {...},
  "currentFragment": {
    "code": "existing code...",
    "file_path": "pages/index.tsx",
    ...
  }
}
```

## Connecting to Frontend

Update your Next.js frontend to call the Python backend by:

1. Setting the `NEXT_PUBLIC_API_URL` environment variable in `.env.local`:
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

2. Or modify the API calls in `app/page.tsx` to point to the Python backend.

## Project Structure

```
backend/
├── main.py           # FastAPI application with routes
├── schemas.py        # Pydantic models
├── templates.py      # Template definitions
├── llm_clients.py    # LLM provider clients
├── requirements.txt  # Python dependencies
├── .env.example      # Example environment variables
└── README.md         # This file
```

