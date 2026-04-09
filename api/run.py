import uvicorn
import os
import sys

if __name__ == "__main__":
    # Add parent directory to path to allow imports
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    # Run the app on port 8002 since 8000 and 8001 are taken
    uvicorn.run("main:app", host="0.0.0.0", port=8002, reload=True)