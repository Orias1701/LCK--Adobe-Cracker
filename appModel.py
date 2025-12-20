# root/llama_run.py

import json
import sys, os
import time
import subprocess

from pathlib import Path
from huggingface_hub import hf_hub_download

# ==============================

BASE = Path(getattr(sys, "_MEIPASS", Path(__file__).parent))

CONFIG = BASE/"Config"/"config.json"
with open(CONFIG, "r", encoding="utf-8") as f:
    cfg = json.load(f)

# CONFIG ======================================================
model_dir = cfg['paths']['local_model_dir']
llms_dir = cfg['paths']['local_llms_dir']
publisher = cfg['models']['responding_model']['publisher']
model_type = cfg['models']['responding_model']['model_type']
hf_repo_id = cfg['models']['responding_model']['hf_repo_id']
hf_filename = cfg['models']['responding_model']['hf_filename']

LLMS_DIR = Path(BASE/model_dir/llms_dir/publisher/model_type)
LLMS_FILE = hf_filename
PORT = "8080"
CONTAINER_NAME = "local-llama-gpu"
IMAGE = "ghcr.io/ggerganov/llama.cpp:server-cuda"
# ============================================================

# Ensure model directory exists
LLMS_DIR.mkdir(parents=True, exist_ok=True)

model_path = LLMS_DIR / LLMS_FILE

# Auto-download if missing
if not model_path.exists():
    print(f"❗ Model not found locally, downloading from HuggingFace: {hf_repo_id}")
    try:
        downloaded = hf_hub_download(
            repo_id=hf_repo_id,
            filename=hf_filename,
            local_dir=LLMS_DIR,
            local_dir_use_symlinks=False
        )
        print(f"✅ Downloaded model to: {downloaded}")
    except Exception as e:
        print(f"❌ Failed to download model: {e}")
        sys.exit(1)
else:
    print(f"✅ Model found: {model_path}")

# Ensure Docker Desktop is running
def is_docker_running():
    try:
        out = subprocess.check_output("docker info", shell=True, stderr=subprocess.STDOUT)
        return b"Server Version" in out
    except:
        return False

def start_docker_desktop():
    print("🚀 Starting Docker Desktop...")
    docker_path = r"C:\Program Files\Docker\Docker\Docker Desktop.exe"
    if not Path(docker_path).exists():
        print("❌ Docker Desktop not found. Update path!")
        sys.exit(1)
    subprocess.Popen(f'"{docker_path}"')
    time.sleep(5)

if not is_docker_running():
    start_docker_desktop()
    while not is_docker_running():
        print("⏳ Waiting for Docker to start...")
        time.sleep(3)

print("✅ Docker is ready")

print("🛑 Removing previous container (if any)")
os.system(f"docker rm -f {CONTAINER_NAME} >nul 2>&1")

cmd = (
    f'docker run --gpus all --name {CONTAINER_NAME} -p {PORT}:8080 '
    f'-e GGML_CUDA=1 -e GGML_CUDA_FORCE_MMQ=1 -e GGML_CUDA_SCRATCH_SIZE_MB=4096 '
    f'-v "{LLMS_DIR}:/models" {IMAGE} '
    f'--model /models/{LLMS_FILE} --n-gpu-layers 999 --ctx-size 4096'
)

print("🚀 Starting Llama server...")
print(cmd)

subprocess.Popen(cmd, shell=True)
time.sleep(3)

print(f"""
✅ Llama server started!
URL: http://localhost:{PORT}
Model: {LLMS_FILE}
Press Ctrl+C to stop.
""")
