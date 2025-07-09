"""
Constants for the MiraMind API
"""

import os

# Path to frontend public directory for static files
FRONTEND_PUBLIC_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "frontend", "public")
)

# Path to Next.js static files directory
NEXTJS_STATIC_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "frontend", ".next", "static")
)

# Path to the chat script
SCRIPT_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "llm", "langgraph", "run_chat.py")
)

# CORS settings
CORS_ORIGINS = ["*"]
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_METHODS = ["*"]
CORS_ALLOW_HEADERS = ["*"]

# Timeout settings
SCRIPT_EXECUTION_TIMEOUT = 60  # seconds
