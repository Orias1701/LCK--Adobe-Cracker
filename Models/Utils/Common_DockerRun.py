import sys
import time
import requests
import subprocess

from pathlib import Path

def isDockerRunning():
    try:
        out = subprocess.check_output("docker info", shell=True, stderr=subprocess.STDOUT)
        return b"Server Version" in out
    except:
        return False
    
def startDocker(DOCKER_PATH):
    print("🚀 Starting Docker Desktop...")
    if not Path(DOCKER_PATH).exists():
        print("❌ Docker Desktop not found!")
        sys.exit(1)
    subprocess.Popen(f'"{DOCKER_PATH}"')
    time.sleep(5)
    
def dockerEnsure(DOCKER_PATH):
    if not isDockerRunning():
        startDocker(DOCKER_PATH)
        while not isDockerRunning():
            print("⏳ Waiting for Docker to start...")
            time.sleep(5)
    else: 
        print("✅ Docker is ready")
        
def serverWait(url, sc_msg, timeout=60):
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = requests.get(url)
            if response.status_code == 200:
                print(sc_msg)
                return
        except requests.exceptions.ConnectionError:
            pass
        
        time.sleep(1)
    
    raise RuntimeError("Server failed to start")