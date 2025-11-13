import subprocess
import sys
import os

def run_local_qdrant_server():
    """
    Runs the 'qdrant' executable located in the same directory as this script.
    """
    # The path to the executable is in the current directory
    qdrant_exec_path = os.path.join(os.path.dirname(__file__), "qdrant")

    if not os.path.exists(qdrant_exec_path):
        print(f"Error: Qdrant executable not found at '{qdrant_exec_path}'")
        print("Please download the qdrant binary from GitHub releases and place it in the same directory as this script.")
        sys.exit(1)

    print(f"Found Qdrant executable at: {qdrant_exec_path}")
    print("\nStarting local Qdrant server...")
    print("This terminal will now show server logs. Keep it running.")
    print("To stop the server, press Ctrl+C in this terminal.")

    process = None
    try:
        # Start the server process
        process = subprocess.Popen(
            [qdrant_exec_path],
            stdout=sys.stdout,
            stderr=sys.stderr,
        )
        process.wait()
    except KeyboardInterrupt:
        print("\nCtrl+C received. Shutting down Qdrant server...")
        if process:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                print("Server did not terminate gracefully, forcing kill.")
                process.kill()
            print("Server shut down.")
    except Exception as e:
        print(f"An error occurred while running the server: {e}")

if __name__ == "__main__":
    run_local_qdrant_server()