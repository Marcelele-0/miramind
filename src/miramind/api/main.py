from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import subprocess
import json
import os

from miramind.shared.logger import logger

app = FastAPI()

# Allow frontend requests (adjust origin in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Input model for chat
class ChatInput(BaseModel):
    userInput: str
    chatHistory: list = []
    memory: str = ""

# Absolute path to run_chat.py
SCRIPT_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "llm", "langgraph", "run_chat.py")
)

@app.post("/api/chat/start")
async def start_call():
    logger.info("Starting chat call...")
    # Optional init actions
    return {"message": "Call started."}

@app.post("/api/chat/message")
async def chat_message(input: ChatInput):
    try:
        input_json = json.dumps({
            "text": input.userInput,
            "chat_history": input.chatHistory,
            "memory": input.memory
        })

        result = subprocess.run(
            ["python", SCRIPT_PATH, input_json],
            capture_output=True,
            text=True
        )
        logger.debug(f"Running script: {SCRIPT_PATH} with input: {input_json}")

        if result.returncode != 0:
            return JSONResponse(status_code=500, content={"error": result.stderr})
        logger.debug(f"STDOUT: {result.stdout}")
        logger.debug(f"STDERR: {result.stderr}")
        logger.debug(f"RETURNCODE: {result.returncode}")

        response = json.loads(result.stdout)
        return response

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
