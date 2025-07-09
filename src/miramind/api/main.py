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
    sessionId: str = None  # Add session tracking


# Global variable to track current session
current_session_id = None


@app.post("/api/chat/start")
async def start_call():
    """Start a new call session"""
    global current_session_id
    import uuid
    from datetime import datetime
    
    # Generate new session ID
    current_session_id = str(uuid.uuid4())
    
    logger.info(f"Starting new chat session: {current_session_id}")
    
    # Save session start to a sessions file
    sessions_log_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
        "sessions_log.json"
    )
    
    session_data = {
        "sessionId": current_session_id,
        "startTime": datetime.now().isoformat(),
        "messages": []
    }
    
    try:
        # Load existing sessions or create new list
        if os.path.exists(sessions_log_path):
            with open(sessions_log_path, 'r', encoding='utf-8') as f:
                sessions = json.load(f)
        else:
            sessions = []
        
        sessions.append(session_data)
        
        # Save sessions
        with open(sessions_log_path, 'w', encoding='utf-8') as f:
            json.dump(sessions, f, indent=2, ensure_ascii=False)
            
    except Exception as e:
        logger.error(f"Error saving session start: {e}")
    
    return {"message": "Call started", "sessionId": current_session_id}


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
    global current_session_id
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
            
            # Save message to current session
            if current_session_id:
                # The emotion and confidence should come from the chatbot state, 
                # but since the script doesn't return them, we'll need to read from emotion_log
                # or implement a way to get them from the script
                emotion = "neutral"  # Default
                confidence = 0.0     # Default
                
                # Try to read the latest emotion from emotion_log.json
                try:
                    emotion_log_path = os.path.join(
                        os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                        "emotion_log.json"
                    )
                    if os.path.exists(emotion_log_path):
                        with open(emotion_log_path, 'r', encoding='utf-8') as f:
                            emotion_data = json.load(f)
                            if emotion_data:
                                # Get the last entry that matches our input
                                for entry in reversed(emotion_data):
                                    if entry.get("input", "").strip().lower() == input.userInput.strip().lower():
                                        emotion = entry.get("emotion", "neutral")
                                        confidence = entry.get("confidence", 0.0)
                                        break
                except Exception as e:
                    logger.error(f"Error reading emotion from log: {e}")
                
                await save_message_to_session(
                    current_session_id, 
                    input.userInput, 
                    response.get("response_text", ""),
                    emotion,
                    confidence
                )
            
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


async def save_message_to_session(session_id: str, user_input: str, bot_response: str, emotion: str, confidence: float):
    """Save a message exchange to the current session"""
    try:
        from datetime import datetime
        
        sessions_log_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
            "sessions_log.json"
        )
        
        if not os.path.exists(sessions_log_path):
            return
            
        with open(sessions_log_path, 'r', encoding='utf-8') as f:
            sessions = json.load(f)
        
        # Find current session and add message
        for session in sessions:
            if session["sessionId"] == session_id:
                message_exchange = {
                    "timestamp": datetime.now().isoformat(),
                    "userInput": user_input,
                    "emotion": emotion,
                    "confidence": confidence,
                    "botResponse": bot_response
                }
                session["messages"].append(message_exchange)
                break
        
        # Save updated sessions
        with open(sessions_log_path, 'w', encoding='utf-8') as f:
            json.dump(sessions, f, indent=2, ensure_ascii=False)
            
    except Exception as e:
        logger.error(f"Error saving message to session: {e}")


@app.get("/api/transcripts")
async def get_transcripts():
    """Get all conversation transcripts from session logs, grouped by actual call sessions"""
    try:
        # Path to sessions log file
        sessions_log_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
            "sessions_log.json"
        )
        
        if not os.path.exists(sessions_log_path):
            logger.warning(f"Sessions log file not found: {sessions_log_path}")
            return {"transcripts": []}
        
        with open(sessions_log_path, 'r', encoding='utf-8') as f:
            sessions = json.load(f)
        
        # Transform sessions into transcript format
        transcripts = []
        for i, session in enumerate(sessions):
            if not session.get("messages"):
                continue  # Skip sessions with no messages
                
            messages = session["messages"]
            
            # Calculate session metadata
            session_emotions = [msg.get("emotion", "neutral") for msg in messages]
            most_common_emotion = max(set(session_emotions), key=session_emotions.count) if session_emotions else "neutral"
            avg_confidence = sum(msg.get("confidence", 0.0) for msg in messages) / len(messages) if messages else 0.0
            
            # Create conversation exchanges
            conversation = []
            for msg in messages:
                conversation.append({
                    "type": "user",
                    "content": msg.get("userInput", ""),
                    "emotion": msg.get("emotion", "neutral"),
                    "confidence": msg.get("confidence", 0.0),
                    "timestamp": msg.get("timestamp", "")
                })
                conversation.append({
                    "type": "assistant", 
                    "content": msg.get("botResponse", ""),
                    "timestamp": msg.get("timestamp", "")
                })
            
            # Calculate session duration (mock for now)
            duration_minutes = len(messages) * 2 + (i % 3)
            duration_seconds = (i * 15) % 60
            
            transcript = {
                "id": session.get("sessionId", f"session_{i}"),
                "timestamp": session.get("startTime", "2025-01-09T14:00:00Z"),
                "conversation": conversation,
                "primaryEmotion": most_common_emotion,
                "averageConfidence": avg_confidence,
                "messageCount": len(messages),
                "duration": f"{duration_minutes}:{duration_seconds:02d}"
            }
            transcripts.append(transcript)
        
        # Sort by timestamp (most recent first)
        transcripts.sort(key=lambda x: x["timestamp"], reverse=True)
        
        logger.info(f"Returning {len(transcripts)} call sessions")
        return {"transcripts": transcripts}
        
    except Exception as e:
        logger.error(f"Error loading transcripts: {e}")
        return JSONResponse(status_code=500, content={"error": "Failed to load transcripts"})


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
