import asyncio
import json
import os
import subprocess
import threading
import time
import uuid
from datetime import datetime
from queue import Queue
from typing import Optional

from fastapi import BackgroundTasks, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from openai import OpenAI
from pydantic import BaseModel

from miramind.api.const import (
    CORS_ALLOW_CREDENTIALS,
    CORS_ALLOW_HEADERS,
    CORS_ALLOW_METHODS,
    CORS_ORIGINS,
    FRONTEND_PUBLIC_PATH,
    NEXTJS_STATIC_PATH,
    SCRIPT_EXECUTION_TIMEOUT,
    SCRIPT_PATH,
)
from miramind.audio.stt.stt_class import STT
from miramind.audio.stt.stt_threads import timed_listen_and_transcribe

# Import chatbot directly for faster processing
from miramind.llm.langgraph.chatbot import get_chatbot
from miramind.llm.langgraph.run_chat import process_chat_message_async
from miramind.shared.logger import logger

app = FastAPI()

# Initialize OpenAI client for STT
try:
    from dotenv import load_dotenv

    load_dotenv()

    # Fix SSL certificate issue on Windows
    import ssl

    ssl_cert_file = os.environ.get('SSL_CERT_FILE')
    if ssl_cert_file and not os.path.exists(ssl_cert_file):
        logger.warning(f"SSL_CERT_FILE points to non-existent path: {ssl_cert_file}")
        os.environ.pop('SSL_CERT_FILE', None)

    openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    logger.info("OpenAI client initialized for STT")
except Exception as e:
    logger.error(f"Failed to initialize OpenAI client: {e}")
    openai_client = None

# Mount static files for audio
if os.path.exists(FRONTEND_PUBLIC_PATH):
    app.mount("/static", StaticFiles(directory=FRONTEND_PUBLIC_PATH), name="static")
    logger.info(f"Mounted static files from: {FRONTEND_PUBLIC_PATH}")
else:
    logger.warning(f"Frontend public directory not found: {FRONTEND_PUBLIC_PATH}")

# Mount Next.js static files
if os.path.exists(NEXTJS_STATIC_PATH):
    app.mount("/_next/static", StaticFiles(directory=NEXTJS_STATIC_PATH), name="nextjs_static")
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


# New input model for voice recording
class VoiceRecordingInput(BaseModel):
    duration: int = 10  # Recording duration in seconds
    chunk_duration: int = 5  # Chunk duration for processing
    lag: int = 2  # Lag between threads
    sessionId: str = None


# Input model for voice chat (combines STT + chat)
class VoiceChatInput(BaseModel):
    audioData: Optional[str] = None  # Base64 encoded audio data
    chatHistory: list = []
    memory: str = ""
    sessionId: str = None


# Global variable to track current session
current_session_id = None

# Store for ongoing voice recordings
voice_recordings = {}  # session_id -> recording_data


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
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "sessions_log.json"
    )

    session_data = {
        "sessionId": current_session_id,
        "startTime": datetime.now().isoformat(),
        "messages": [],
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
            audio_path,
            media_type="audio/wav",
            headers={
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0",
            },
        )
    else:
        return JSONResponse(status_code=404, content={"error": "Audio file not found"})


@app.get("/output.wav")
async def get_audio_file_simple():
    """Simple endpoint to serve the audio file"""
    audio_path = os.path.join(FRONTEND_PUBLIC_PATH, "output.wav")
    if os.path.exists(audio_path):
        return FileResponse(
            audio_path,
            media_type="audio/wav",
            headers={
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0",
            },
        )
    else:
        return JSONResponse(status_code=404, content={"error": "Audio file not found"})


@app.post("/api/chat/message")
async def chat_message(input: ChatInput, background_tasks: BackgroundTasks):
    global current_session_id
    logger.info(f"Received chat message: {input.userInput}")

    start_time = time.time()

    try:
        # Check cache first
        cache_key = _get_cache_key(input.userInput, len(input.chatHistory))
        if cache_key in api_response_cache:
            cached_data, timestamp = api_response_cache[cache_key]
            if _is_cache_valid(timestamp):
                logger.info(f"API cache hit for: {input.userInput[:30]}...")
                cached_data["processing_time"] = time.time() - start_time
                cached_data["cached"] = True
                return cached_data

        # Use direct async chatbot call for much faster processing
        # Optimize chat history - only keep last 6 messages for faster processing
        optimized_history = (
            input.chatHistory[-6:] if len(input.chatHistory) > 6 else input.chatHistory
        )

        # Call chatbot directly using async version
        result = await process_chat_message_async(
            user_input_text=input.userInput, chat_history=optimized_history, memory=input.memory
        )

        processing_time = time.time() - start_time
        logger.info(f"Direct chatbot call completed in {processing_time:.2f}s")

        # Return response immediately without waiting for session logging
        response_data = {
            "response_text": result.get("response_text", ""),
            "audio_file_path": result.get("audio_file_path"),
            "memory": result.get("memory", input.memory),
            "processing_time": processing_time,
        }

        # Cache the response
        api_response_cache[cache_key] = (response_data, time.time())

        # Add background task for session logging (non-blocking)
        if current_session_id:
            background_tasks.add_task(
                save_message_to_session_async,
                current_session_id,
                input.userInput,
                result.get("response_text", ""),
                "neutral",  # Will be updated with actual emotion in background
                0.0,
            )

        return response_data

    except Exception as e:
        logger.error(f"Optimized chatbot error: {e}")
        # Fallback to subprocess if direct call fails
        return await chat_message_fallback(input)


async def chat_message_fallback(input: ChatInput):
    """Fallback to subprocess method if direct call fails"""
    global current_session_id
    logger.info("Using fallback subprocess method")

    try:
        input_json = json.dumps(
            {
                "text": input.userInput,
                "chat_history": input.chatHistory[-4:],  # Limit context for faster processing
                "memory": input.memory,
            }
        )

        logger.debug(f"Running script: {SCRIPT_PATH} with input: {input_json}")

        # Use asyncio.create_subprocess_exec for async subprocess
        proc = await asyncio.create_subprocess_exec(
            "python",
            SCRIPT_PATH,
            input_json,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        )

        try:
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(), timeout=30.0
            )  # Reduced timeout
        except asyncio.TimeoutError:
            proc.kill()
            await proc.wait()
            logger.error("Script execution timed out")
            return JSONResponse(status_code=500, content={"error": "Script execution timed out"})

        if proc.returncode != 0:
            logger.error(f"Script failed with return code {proc.returncode}")
            logger.error(f"STDERR: {stderr.decode()}")
            return JSONResponse(status_code=500, content={"error": stderr.decode()})

        # Parse JSON from the last line of stdout
        stdout_lines = stdout.decode().strip().split("\n")
        json_line = stdout_lines[-1]

        try:
            response = json.loads(json_line)
            logger.info(f"Successfully parsed fallback response")
            return response
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from stdout: {e}")
            return JSONResponse(status_code=500, content={"error": "Failed to parse response JSON"})

    except Exception as e:
        logger.error(f"Fallback error: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})


async def save_message_to_session_async(
    session_id: str, user_input: str, bot_response: str, emotion: str, confidence: float
):
    """Async version of save_message_to_session for background processing"""
    try:
        from datetime import datetime

        sessions_log_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "sessions_log.json"
        )

        if not os.path.exists(sessions_log_path):
            return

        # Run file I/O in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            _save_session_sync,
            sessions_log_path,
            session_id,
            user_input,
            bot_response,
            emotion,
            confidence,
        )

    except Exception as e:
        logger.error(f"Error saving message to session (async): {e}")


def _save_session_sync(
    sessions_log_path, session_id, user_input, bot_response, emotion, confidence
):
    """Synchronous helper for file operations"""
    from datetime import datetime

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
                "botResponse": bot_response,
            }
            session["messages"].append(message_exchange)
            break

    # Save updated sessions
    with open(sessions_log_path, 'w', encoding='utf-8') as f:
        json.dump(sessions, f, indent=2, ensure_ascii=False)


async def save_message_to_session(
    session_id: str, user_input: str, bot_response: str, emotion: str, confidence: float
):
    """Save a message exchange to the current session"""
    try:
        from datetime import datetime

        sessions_log_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "sessions_log.json"
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
                    "botResponse": bot_response,
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
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "sessions_log.json"
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
            most_common_emotion = (
                max(set(session_emotions), key=session_emotions.count)
                if session_emotions
                else "neutral"
            )
            avg_confidence = (
                sum(msg.get("confidence", 0.0) for msg in messages) / len(messages)
                if messages
                else 0.0
            )

            # Create conversation exchanges
            conversation = []
            for msg in messages:
                conversation.append(
                    {
                        "type": "user",
                        "content": msg.get("userInput", ""),
                        "emotion": msg.get("emotion", "neutral"),
                        "confidence": msg.get("confidence", 0.0),
                        "timestamp": msg.get("timestamp", ""),
                    }
                )
                conversation.append(
                    {
                        "type": "assistant",
                        "content": msg.get("botResponse", ""),
                        "timestamp": msg.get("timestamp", ""),
                    }
                )

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
                "duration": f"{duration_minutes}:{duration_seconds:02d}",
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


# Removed duplicate endpoints - using new voice endpoints instead


@app.post("/api/voice/upload")
async def upload_voice(file: UploadFile = File(...)):
    """Upload and transcribe voice file"""
    if not openai_client:
        raise HTTPException(status_code=500, detail="OpenAI client not initialized")

    try:
        # Validate file type
        if not file.content_type.startswith('audio/'):
            raise HTTPException(status_code=400, detail="File must be an audio file")

        # Read audio data
        audio_data = await file.read()

        # Create STT instance and transcribe
        stt = STT(client=openai_client, logger=logger)

        # Create a file-like object for the STT
        import io

        audio_buffer = io.BytesIO(audio_data)
        audio_buffer.name = file.filename or "audio.wav"

        # Transcribe the audio
        transcript_result = stt.transcribe_bytes(audio_buffer)

        logger.info(f"Voice transcription: {transcript_result}")

        return {
            "transcript": transcript_result.get("transcript", ""),
            "filename": file.filename,
            "success": True,
        }

    except Exception as e:
        logger.error(f"Voice upload error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/voice/start-recording")
async def start_voice_recording(input: VoiceRecordingInput):
    """Start voice recording session"""
    if not openai_client:
        raise HTTPException(status_code=500, detail="OpenAI client not initialized")

    try:
        # Generate recording session ID if not provided
        recording_id = input.sessionId or str(uuid.uuid4())

        # Store recording session data
        voice_recordings[recording_id] = {
            "status": "recording",
            "duration": input.duration,
            "chunk_duration": input.chunk_duration,
            "lag": input.lag,
            "start_time": datetime.now().isoformat(),
            "transcripts": [],
        }

        logger.info(f"Started voice recording session: {recording_id}")

        return {
            "recording_id": recording_id,
            "status": "recording",
            "duration": input.duration,
            "message": "Voice recording started",
        }

    except Exception as e:
        logger.error(f"Start recording error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/voice/stop-recording/{recording_id}")
async def stop_voice_recording(recording_id: str, background_tasks: BackgroundTasks):
    """Stop voice recording and get transcripts"""
    if recording_id not in voice_recordings:
        raise HTTPException(status_code=404, detail="Recording session not found")

    try:
        recording_data = voice_recordings[recording_id]
        recording_data["status"] = "stopped"
        recording_data["end_time"] = datetime.now().isoformat()

        # Add background task to clean up old recordings
        background_tasks.add_task(cleanup_old_recordings)

        logger.info(f"Stopped voice recording session: {recording_id}")

        return {
            "recording_id": recording_id,
            "status": "stopped",
            "transcripts": recording_data.get("transcripts", []),
            "duration": recording_data.get("duration", 0),
        }

    except Exception as e:
        logger.error(f"Stop recording error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/voice/record-and-transcribe")
async def record_and_transcribe(input: VoiceRecordingInput):
    """Record voice for specified duration and transcribe"""
    if not openai_client:
        raise HTTPException(status_code=500, detail="OpenAI client not initialized")

    try:
        logger.info(f"Starting voice recording for {input.duration} seconds")

        # Use the timed_listen_and_transcribe function
        transcript_buffer = timed_listen_and_transcribe(
            client=openai_client,
            duration=input.duration,
            chunk_duration=input.chunk_duration,
            lag=input.lag,
            timeout=10,
        )

        # Extract all transcripts from buffer
        transcripts = []
        while not transcript_buffer.empty():
            try:
                transcript_data = transcript_buffer.get_nowait()
                transcripts.append(transcript_data)
            except:
                break

        # Combine all transcripts
        combined_transcript = " ".join(
            [t.get("transcript", "") for t in transcripts if t.get("transcript")]
        )

        logger.info(f"Voice recording completed. Combined transcript: {combined_transcript}")

        return {
            "transcript": combined_transcript,
            "individual_transcripts": transcripts,
            "duration": input.duration,
            "success": True,
        }

    except Exception as e:
        logger.error(f"Record and transcribe error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/voice/chat")
async def voice_chat(input: VoiceChatInput, background_tasks: BackgroundTasks):
    """Process voice input and return chat response with optimizations"""
    global current_session_id

    if not openai_client:
        raise HTTPException(status_code=500, detail="OpenAI client not initialized")

    start_time = time.time()

    try:
        transcript = ""

        # If audio data provided, transcribe it first
        if input.audioData:
            import base64
            import io

            # Decode base64 audio data
            audio_bytes = base64.b64decode(input.audioData)
            audio_buffer = io.BytesIO(audio_bytes)
            audio_buffer.name = "voice_input.wav"

            # Transcribe using async if possible
            stt = STT(client=openai_client, logger=logger)
            transcript_result = stt.transcribe_bytes(audio_buffer)
            transcript = transcript_result.get("transcript", "")

            logger.info(f"Voice chat transcription: {transcript}")

        if not transcript:
            raise HTTPException(status_code=400, detail="No transcript available")

        # Use optimized chat processing
        optimized_history = (
            input.chatHistory[-6:] if len(input.chatHistory) > 6 else input.chatHistory
        )

        # Call chatbot directly using async version
        result = await process_chat_message_async(
            user_input_text=transcript, chat_history=optimized_history, memory=input.memory
        )

        processing_time = time.time() - start_time
        logger.info(f"Voice chat completed in {processing_time:.2f}s")

        # Prepare response with transcript
        response_data = {
            "response_text": result.get("response_text", ""),
            "audio_file_path": result.get("audio_file_path"),
            "memory": result.get("memory", input.memory),
            "transcript": transcript,
            "processing_time": processing_time,
        }

        # Add background task for session logging (non-blocking)
        if current_session_id:
            background_tasks.add_task(
                save_message_to_session_async,
                current_session_id,
                f"🎤 {transcript}",  # Mark as voice input
                result.get("response_text", ""),
                "neutral",
                0.0,
            )

        return response_data

    except Exception as e:
        logger.error(f"Voice chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def cleanup_old_recordings():
    """Clean up old recording sessions"""
    try:
        current_time = datetime.now()
        expired_sessions = []

        for session_id, data in voice_recordings.items():
            start_time = datetime.fromisoformat(data.get("start_time", current_time.isoformat()))
            if (current_time - start_time).total_seconds() > 3600:  # 1 hour
                expired_sessions.append(session_id)

        for session_id in expired_sessions:
            del voice_recordings[session_id]

        if expired_sessions:
            logger.info(f"Cleaned up {len(expired_sessions)} expired recording sessions")

    except Exception as e:
        logger.error(f"Error cleaning up recordings: {e}")


# Simple API-level cache for common responses
api_response_cache = {}
API_CACHE_SIZE = 50
API_CACHE_TTL = 300  # 5 minutes


def _get_cache_key(user_input: str, history_length: int) -> str:
    """Generate cache key for API responses"""
    import hashlib

    content = f"{user_input.lower().strip()}_{history_length}"
    return hashlib.md5(content.encode()).hexdigest()


def _is_cache_valid(timestamp: float) -> bool:
    """Check if cache entry is still valid"""
    return (time.time() - timestamp) < API_CACHE_TTL


def _cleanup_api_cache():
    """Remove expired entries from API cache"""
    current_time = time.time()
    expired_keys = [
        key
        for key, (data, timestamp) in api_response_cache.items()
        if not _is_cache_valid(timestamp)
    ]
    for key in expired_keys:
        del api_response_cache[key]

    # Also limit cache size
    if len(api_response_cache) > API_CACHE_SIZE:
        # Remove oldest entries
        sorted_items = sorted(api_response_cache.items(), key=lambda x: x[1][1])
        for key, _ in sorted_items[: len(api_response_cache) - API_CACHE_SIZE]:
            del api_response_cache[key]


# Background task to clean cache periodically
async def periodic_cache_cleanup():
    """Periodic cleanup of API cache"""
    while True:
        try:
            _cleanup_api_cache()
            await asyncio.sleep(60)  # Clean every minute
        except Exception as e:
            logger.error(f"Cache cleanup error: {e}")
            await asyncio.sleep(60)


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    try:
        # Pre-initialize chatbot
        chatbot_instance = get_chatbot()
        logger.info("Chatbot pre-initialized for faster responses")

        # Start cache cleanup task
        asyncio.create_task(periodic_cache_cleanup())

        logger.info("FastAPI startup completed with optimizations")
    except Exception as e:
        logger.error(f"Startup error: {e}")
