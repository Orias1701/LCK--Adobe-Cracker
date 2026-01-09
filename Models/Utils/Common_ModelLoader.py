import sys
from huggingface_hub import hf_hub_download

def modelLoad(LLMS_PATH, MODEL_REPO, MODEL_FILE, LLMS_DIR):
    if not LLMS_PATH.exists():
        print(f"❗ Model not found locally, downloading from HuggingFace: {MODEL_REPO}")
        try:
            downloaded = hf_hub_download(
                repo_id=MODEL_REPO,
                filename=MODEL_FILE,
                local_dir=LLMS_DIR,
                local_dir_use_symlinks=False
            )
            print(f"✅ Downloaded model to: {downloaded}")
        except Exception as e:
            print(f"❌ Failed to download model: {e}")
            sys.exit(1)
    else:
        print(f"✅ Model found: {LLMS_PATH}")