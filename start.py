import uvicorn
import webbrowser
import threading
import time
import os

def open_browser():
    time.sleep(10)
    file_path = os.path.abspath("Demo/index.html")
    webbrowser.open(f"file://{file_path}")

if __name__ == "__main__":
    threading.Thread(target=open_browser).start()
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)