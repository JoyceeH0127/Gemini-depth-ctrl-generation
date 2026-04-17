from google import genai
import os
import sys

# Add parent directory to path to import config
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import Config

def list_models():
    # Force Vertex AI client
    client = genai.Client(
        vertexai=True, 
        project=Config.PROJECT_ID or os.getenv("GOOGLE_CLOUD_PROJECT"), 
        location=Config.LOCATION or "us-central1"
    )
    
    print(f"Listing models for Project: {Config.PROJECT_ID}, Location: {Config.LOCATION}...")
    
    try:
        # Pager object
        pager = client.models.list(config={"page_size": 100}) 
        print("\nFound models:")
        for model in pager:
            # Filter somewhat for brevity? No, user needs to see all "Gemini" ones.
            if "gemini" in model.name.lower():
                print(f" - {model.name} (Display: {model.display_name})")
    except Exception as e:
        print(f"Error listing models: {e}")

if __name__ == "__main__":
    list_models()
