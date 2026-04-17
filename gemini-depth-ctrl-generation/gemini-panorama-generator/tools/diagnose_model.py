from google import genai
import os
import sys
import traceback

# Add parent directory to path to import config
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import Config

def try_generate(client, model_name, method_desc):
    print(f"\n--- Testing: {model_name} [{method_desc}] ---")
    try:
        response = client.models.generate_content(
            model=model_name,
            contents="Hello",
            config=None
        )
        print("SUCCESS! Response received.")
        return True
    except Exception as e:
        print(f"FAILED. Error: {e}")
        return False

def diagnose():
    project_id = Config.PROJECT_ID or os.getenv("GOOGLE_CLOUD_PROJECT")
    location = Config.LOCATION or "us-central1"
    
    print(f"Initializing Vertex AI Client for Project: {project_id}, Location: {location}")
    client = genai.Client(vertexai=True, project=project_id, location=location)

    base_name = "gemini-3-pro-image-preview"
    
    # 1. Try short name
    if not try_generate(client, base_name, "Short Name"):
        # 2. Try with publisher prefix
        long_name = f"publishers/google/models/{base_name}"
        if not try_generate(client, long_name, "Publisher Prefix"):
            # 3. Try with full resource name (if project known)
            if project_id:
                full_name = f"projects/{project_id}/locations/{location}/publishers/google/models/{base_name}"
                try_generate(client, full_name, "Full Resource Path")

if __name__ == "__main__":
    diagnose()
