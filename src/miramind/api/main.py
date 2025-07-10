import asyncio
import json
import os
import subprocess
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
                confidence = 0.0  # Default

                # Try to read the latest emotion from emotion_log.json
                try:
                    emotion_log_path = os.path.join(
                        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                        "emotion_log.json",
                    )
                    if os.path.exists(emotion_log_path):
                        with open(emotion_log_path, 'r', encoding='utf-8') as f:
                            emotion_data = json.load(f)
                            if emotion_data:
                                # Get the last entry that matches our input
                                for entry in reversed(emotion_data):
                                    if (
                                        entry.get("input", "").strip().lower()
                                        == input.userInput.strip().lower()
                                    ):
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
                    confidence,
                )

            return response
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from stdout: {e}")
            logger.error(f"JSON line was: {json_line}")
            logger.error(f"Full stdout was: {result.stdout}")
            return JSONResponse(status_code=500, content={"error": "Failed to parse response JSON"})

    except subprocess.TimeoutExpired:
        logger.error("Script execution timed out")
        return JSONResponse(status_code=500, content={"error": "Script execution timed out"})
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})


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
async def voice_chat(input: VoiceChatInput):
    """Process voice input and return chat response"""
    global current_session_id

    if not openai_client:
        raise HTTPException(status_code=500, detail="OpenAI client not initialized")

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

            # Transcribe
            stt = STT(client=openai_client, logger=logger)
            transcript_result = stt.transcribe_bytes(audio_buffer)
            transcript = transcript_result.get("transcript", "")

            logger.info(f"Voice chat transcription: {transcript}")

        if not transcript:
            raise HTTPException(status_code=400, detail="No transcript available")

        # Use the transcript as user input for the chatbot
        chat_input = ChatInput(
            userInput=transcript,
            chatHistory=input.chatHistory,
            memory=input.memory,
            sessionId=input.sessionId,
        )

        # Process through existing chat pipeline
        chat_response = await chat_message(chat_input)

        # Add the transcript to the response
        if hasattr(chat_response, 'body'):
            # If it's a JSONResponse, extract the data
            import json

            response_data = json.loads(chat_response.body.decode())
            response_data['transcript'] = transcript
            return response_data
        else:
            # If it's already a dict, add transcript
            chat_response['transcript'] = transcript
            return chat_response

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
