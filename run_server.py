"""
Startup script for the FastAPI server.
"""
import uvicorn
import os
import sys

# Add the src directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, "src")
sys.path.insert(0, src_dir)

if __name__ == "__main__":
    # Run the FastAPI server
    uvicorn.run(
        "miramind.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
