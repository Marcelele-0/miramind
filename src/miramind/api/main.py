from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import subprocess
import json
import os

from miramind.shared.logger import logger
from miramind.api.const import (
    FRONTEND_PUBLIC_PATH,
    NEXTJS_STATIC_PATH,
    SCRIPT_PATH,
    CORS_ORIGINS,
    CORS_ALLOW_CREDENTIALS,
    CORS_ALLOW_METHODS,
    CORS_ALLOW_HEADERS,
    SCRIPT_EXECUTION_TIMEOUT,
)

app = FastAPI()

# Mount static files for audio
if os.path.exists(FRONTEND_PUBLIC_PATH):
    app.mount("/static", StaticFiles(directory=FRONTEND_PUBLIC_PATH), name="static")
    logger.info(f"Mounted static files from: {FRONTEND_PUBLIC_PATH}")
else:
    logger.warning(f"Frontend public directory not found: {FRONTEND_PUBLIC_PATH}")

# Mount Next.js static files
if os.path.exists(NEXTJS_STATIC_PATH):
    app.mount(
        "/_next/static", StaticFiles(directory=NEXTJS_STATIC_PATH), name="nextjs_static"
    )
    logger.info(f"Mounted Next.js static files from: {NEXTJS_STATIC_PATH}")
else:
    logger.warning(f"Next.js static directory not found: {NEXTJS_STATIC_PATH}")

# Allow frontend requests (adjust origin in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=CORS_ALLOW_CREDENTIALS,
    allow_methods=CORS_ALLOW_METHODS,
    allow_headers=CORS_ALLOW_HEADERS,
)


# Input model for chat
class ChatInput(BaseModel):
    userInput: str
    chatHistory: list = []
    memory: str = ""


@app.post("/api/chat/start")
async def start_call():
    logger.info("Starting chat call...")
    # Optional init actions
    return {"message": "Call started."}


@app.get("/api/test")
async def test_endpoint():
    """Test endpoint to verify API is working"""
    return {"message": "API is working", "timestamp": "2025-07-04"}


@app.get("/api/audio/output.wav")
async def get_audio_file():
    """Direct endpoint to serve the audio file"""
    audio_path = os.path.join(FRONTEND_PUBLIC_PATH, "output.wav")
    if os.path.exists(audio_path):
        return FileResponse(
            audio_path, media_type="audio/wav", headers={"Cache-Control": "no-cache"}
        )
    else:
        return JSONResponse(status_code=404, content={"error": "Audio file not found"})


@app.get("/output.wav")
async def get_audio_file_simple():
    """Simple endpoint to serve the audio file"""
    audio_path = os.path.join(FRONTEND_PUBLIC_PATH, "output.wav")
    if os.path.exists(audio_path):
        return FileResponse(
            audio_path, media_type="audio/wav", headers={"Cache-Control": "no-cache"}
        )
    else:
        return JSONResponse(status_code=404, content={"error": "Audio file not found"})


@app.post("/api/chat/message")
async def chat_message(input: ChatInput):
    logger.info(f"Received chat message: {input.userInput}")

    try:
        input_json = json.dumps(
            {
                "text": input.userInput,
                "chat_history": input.chatHistory,
                "memory": input.memory,
            }
        )

        logger.debug(f"Running script: {SCRIPT_PATH} with input: {input_json}")

        result = subprocess.run(
            ["python", SCRIPT_PATH, input_json],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(
                os.path.dirname(os.path.dirname(__file__))
            ),  # Set working directory to miramind root
            timeout=SCRIPT_EXECUTION_TIMEOUT,  # Add timeout to prevent hanging
        )

        logger.debug(f"Subprocess completed with return code: {result.returncode}")
        logger.debug(f"STDOUT: {result.stdout}")
        logger.debug(f"STDERR: {result.stderr}")

        if result.returncode != 0:
            logger.error(f"Script failed with return code {result.returncode}")
            logger.error(f"STDERR: {result.stderr}")
            return JSONResponse(status_code=500, content={"error": result.stderr})

        # Parse JSON from the last line of stdout (logging appears before JSON)
        stdout_lines = result.stdout.strip().split("\n")
        json_line = stdout_lines[-1]  # Last line should be the JSON response

        logger.debug(f"Attempting to parse JSON from: {json_line}")

        try:
            response = json.loads(json_line)
            logger.info(f"Successfully parsed response: {response}")
            return response
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from stdout: {e}")
            logger.error(f"JSON line was: {json_line}")
            logger.error(f"Full stdout was: {result.stdout}")
            return JSONResponse(
                status_code=500, content={"error": "Failed to parse response JSON"}
            )

    except subprocess.TimeoutExpired:
        logger.error("Script execution timed out")
        return JSONResponse(
            status_code=500, content={"error": "Script execution timed out"}
        )
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.get("/api/debug/files")
async def debug_files():
    """Debug endpoint to check file system state"""
    info = {
        "frontend_public_path": FRONTEND_PUBLIC_PATH,
        "frontend_public_exists": os.path.exists(FRONTEND_PUBLIC_PATH),
        "files_in_public": [],
        "output_wav_info": {},
    }

    if os.path.exists(FRONTEND_PUBLIC_PATH):
        try:
            info["files_in_public"] = os.listdir(FRONTEND_PUBLIC_PATH)
        except Exception as e:
            info["files_in_public"] = f"Error listing files: {e}"

    output_wav_path = os.path.join(FRONTEND_PUBLIC_PATH, "output.wav")
    if os.path.exists(output_wav_path):
        stat = os.stat(output_wav_path)
        info["output_wav_info"] = {
            "exists": True,
            "size": stat.st_size,
            "modified": stat.st_mtime,
            "path": output_wav_path,
        }
    else:
        info["output_wav_info"] = {"exists": False, "path": output_wav_path}

    return info
