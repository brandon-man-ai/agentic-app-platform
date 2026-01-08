"""FastAPI backend for the Agentic App Platform."""

import os
import json
import asyncio
from typing import Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from dotenv import load_dotenv
from e2b_code_interpreter import Sandbox

from schemas import (
    ChatRequest,
    SandboxRequest,
    FragmentSchema,
    ExecutionResultWeb,
    ExecutionResultInterpreter,
)
from templates import TEMPLATES, to_prompt
from llm_clients import LLMClient, get_fragment_schema, get_morph_edit_schema
from secrets import load_secrets_to_env


# Load environment variables from .env file (for local development)
load_dotenv()

# Load secrets from GCP Secret Manager (if running in GCP)
# This will populate os.environ with secrets from Secret Manager
load_secrets_to_env()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    print("=== API KEYS ===")
    print(f"E2B_API_KEY: {os.getenv('E2B_API_KEY', 'NOT SET')[:15]}..." if os.getenv('E2B_API_KEY') else "E2B_API_KEY: NOT SET")
    print(f"OPENAI_API_KEY: {os.getenv('OPENAI_API_KEY', 'NOT SET')[:10]}..." if os.getenv('OPENAI_API_KEY') else "OPENAI_API_KEY: NOT SET")
    print(f"ANTHROPIC_API_KEY: {os.getenv('ANTHROPIC_API_KEY', 'NOT SET')[:10]}..." if os.getenv('ANTHROPIC_API_KEY') else "ANTHROPIC_API_KEY: NOT SET")
    print("================")
    yield
    # Shutdown
    print("Shutting down...")


app = FastAPI(
    title="Agentic App Platform API",
    description="Python backend for the Agentic App Platform",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Constants
SANDBOX_TIMEOUT_MS = 10 * 60 * 1000  # 10 minutes


@app.get("/")
async def root():
    """Health check endpoint."""
    return {"status": "ok", "message": "Agentic App Platform Python Backend"}


@app.post("/api/chat")
async def chat(request: ChatRequest):
    """
    Generate code using LLM with streaming response.
    
    This endpoint receives a chat request with messages and model configuration,
    then streams back a generated code fragment.
    """
    print(f"userID: {request.userID}")
    print(f"teamID: {request.teamID}")
    print(f"model: {request.model}")
    
    # Display API keys for debugging
    print("=== API KEYS ===")
    print(f"OpenAI API Key (from config): {request.config.apiKey or 'NOT PROVIDED'}")
    print(f"OpenAI API Key (from env): {os.getenv('OPENAI_API_KEY', 'NOT SET')[:10]}..." if os.getenv('OPENAI_API_KEY') else "NOT SET")
    print(f"Anthropic API Key (from env): {os.getenv('ANTHROPIC_API_KEY', 'NOT SET')[:10]}..." if os.getenv('ANTHROPIC_API_KEY') else "NOT SET")
    print("================")
    
    try:
        # Create LLM client
        llm_client = LLMClient(request.model, request.config)
        
        # Get system prompt based on template
        system_prompt = to_prompt(request.template or TEMPLATES)
        
        # Get the schema for structured output
        schema = get_fragment_schema()
        
        async def generate_stream():
            """Generate streaming response."""
            try:
                for chunk in llm_client.generate_structured(
                    system_prompt=system_prompt,
                    messages=request.messages,
                    schema=schema,
                ):
                    yield chunk
            except Exception as e:
                print(f"Error in stream generation: {e}")
                yield json.dumps({"error": str(e)})
        
        return StreamingResponse(
            generate_stream(),
            media_type="text/plain; charset=utf-8",
        )
        
    except Exception as e:
        print(f"Error in chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/sandbox")
async def create_sandbox(request: SandboxRequest):
    """
    Create and run a sandbox with the generated code.
    
    This endpoint receives a code fragment, creates an E2B sandbox,
    installs dependencies, writes the code, and either executes it
    or returns the URL to the running app.
    """
    fragment = request.fragment
    
    print(f"fragment: {fragment}")
    print(f"userID: {request.userID}")
    
    # Display E2B API key
    print("=== E2B API KEY ===")
    e2b_key = os.getenv("E2B_API_KEY")
    print(f"E2B_API_KEY: {e2b_key[:15]}..." if e2b_key else "E2B_API_KEY: NOT SET")
    print("==================")
    fragment.template = "nextjs-developer"
    print("Template: ", fragment.template)
    
    try:
        # Create sandbox
        sbx = Sandbox(
            template=fragment.template,
            metadata={
                "template": fragment.template,
                "userID": request.userID or "",
                "teamID": request.teamID or "",
            },
            api_key=e2b_key,
            timeout=SANDBOX_TIMEOUT_MS // 1000,  # Convert to seconds for Python SDK
        )
        
        print(f"Created sandbox: {sbx.sandbox_id}")
        
        # Install additional dependencies if needed
        if fragment.has_additional_dependencies and fragment.install_dependencies_command:
            result = sbx.commands.run(fragment.install_dependencies_command)
            print(f"Installed dependencies: {', '.join(fragment.additional_dependencies)} in sandbox {sbx.sandbox_id}")
        
        # Write code to filesystem
        sbx.files.write(fragment.file_path, fragment.code)
        print(f"Copied file to {fragment.file_path} in {sbx.sandbox_id}")
        
        # Execute code or return URL
        if fragment.template == "code-interpreter-v1":
            # Execute Python code
            execution = sbx.run_code(fragment.code)
            
            # Convert results to serializable format
            cell_results = []
            for result in execution.results:
                result_dict = {}
                if hasattr(result, 'png') and result.png:
                    result_dict['png'] = result.png
                if hasattr(result, 'text') and result.text:
                    result_dict['text'] = result.text
                if hasattr(result, 'html') and result.html:
                    result_dict['html'] = result.html
                cell_results.append(result_dict)
            
            # Format error if present
            runtime_error = None
            if execution.error:
                runtime_error = {
                    "name": execution.error.name,
                    "value": execution.error.value,
                    "traceback": execution.error.traceback,
                }
            
            return JSONResponse(
                content={
                    "sbxId": sbx.sandbox_id,
                    "template": fragment.template,
                    "stdout": execution.logs.stdout,
                    "stderr": execution.logs.stderr,
                    "runtimeError": runtime_error,
                    "cellResults": cell_results,
                }
            )
        
        # For web apps, return the URL
        port = fragment.port or 80
        url = f"https://{sbx.get_host(port)}"
        
        return JSONResponse(
            content={
                "sbxId": sbx.sandbox_id,
                "template": fragment.template,
                "url": url,
            }
        )
        
    except Exception as e:
        print(f"Error creating sandbox: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/morph-chat")
async def morph_chat(request: ChatRequest):
    """
    Edit existing code using LLM with Morph-style edits.
    
    This endpoint receives a chat request with an existing fragment,
    generates edit instructions, and applies them to create an updated fragment.
    """
    if not request.currentFragment:
        raise HTTPException(status_code=400, detail="currentFragment is required for morph-chat")
    
    current_fragment = request.currentFragment
    
    print(f"Morph edit for file: {current_fragment.file_path}")
    
    try:
        # Create LLM client
        llm_client = LLMClient(request.model, request.config)
        
        # Create contextual system prompt
        system_prompt = f"""You are a code editor. Generate a JSON response with exactly these fields:

{{
  "commentary": "Explain what changes you are making",
  "instruction": "One line description of the change", 
  "edit": "The code changes with // ... existing code ... for unchanged parts",
  "file_path": "{current_fragment.file_path}"
}}

Current file: {current_fragment.file_path}
Current code:
```
{current_fragment.code}
```
"""
        
        # Get edit schema
        schema = get_morph_edit_schema()
        
        # Generate edit instructions (non-streaming for simplicity)
        full_response = ""
        for chunk in llm_client.generate_structured(
            system_prompt=system_prompt,
            messages=request.messages,
            schema=schema,
        ):
            full_response += chunk
        
        # Parse the edit instructions
        try:
            edit_instructions = json.loads(full_response)
        except json.JSONDecodeError:
            raise HTTPException(status_code=500, detail="Failed to parse LLM response as JSON")
        
        # Apply the edits (simplified - in production you'd use Morph API)
        # For now, we'll use a simple replacement based on the edit field
        updated_code = apply_simple_edit(current_fragment.code, edit_instructions.get("edit", ""))
        
        # Create updated fragment
        updated_fragment = {
            **current_fragment.model_dump(),
            "code": updated_code,
            "commentary": edit_instructions.get("commentary", ""),
        }
        
        # Return as streaming response (matching original format)
        async def stream_response():
            yield json.dumps(updated_fragment)
        
        return StreamingResponse(
            stream_response(),
            media_type="text/plain; charset=utf-8",
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in morph-chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def apply_simple_edit(original_code: str, edit: str) -> str:
    """
    Apply a simple edit to the original code.
    
    This is a simplified version - in production you'd use the Morph API
    or a more sophisticated diff/patch algorithm.
    """
    if not edit or "// ... existing code ..." not in edit:
        # If no edit markers, assume it's a full replacement
        return edit if edit else original_code
    
    # Simple implementation: if the edit contains markers,
    # try to apply it as a patch
    # For now, just return the edit with markers removed
    lines = edit.split("\n")
    result_lines = []
    
    for line in lines:
        if "// ... existing code ..." in line or "# ... existing code ..." in line:
            continue
        result_lines.append(line)
    
    return "\n".join(result_lines) if result_lines else original_code


if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=True,
    )

