import subprocess
import sys
import os
from pathlib import Path

def run_server():
    # Get the current directory
    current_dir = Path(__file__).parent.absolute()
    
    try:
        # Start the combined server
        print("Starting server...")
        server_process = subprocess.Popen(
            ["uvicorn", "api.index:app", "--host", "0.0.0.0", "--port", "3000", "--reload"],
            cwd=str(current_dir)
        )
        
        print("\nServer is running!")
        print("Access the application at: http://localhost:3000")
        print("API endpoints are available at: http://localhost:3000/api")
        print("\nPress Ctrl+C to stop the server.")
        
        # Wait for the process
        server_process.wait()
        
    except KeyboardInterrupt:
        print("\nStopping server...")
        server_process.terminate()
        print("Server stopped.")
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    run_server() 