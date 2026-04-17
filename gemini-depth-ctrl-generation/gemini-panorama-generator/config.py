import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    # Google Cloud / Gemini API Configuration
    PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT")
    LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "global")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    
    # Model Configuration
    # Using a high-capability model for multimodal generation
    MODEL_NAME = "gemini-3-pro-image-preview"
    
    # Generation Settings
    OUTPUT_DIR = "outputs"
    
    # Image Dimensions
    PANORAMA_WIDTH = 4096
    PANORAMA_HEIGHT = 2048
    
    CINEMATIC_WIDTH = 3840
    CINEMATIC_HEIGHT = 1640 # 21:9 approx
    
    STANDARD_WIDTH = 3840
    STANDARD_HEIGHT = 2160 # 16:9

    @staticmethod
    def get_model_name():
        return os.getenv("MODEL_NAME", Config.MODEL_NAME)
    
    @staticmethod
    def ensure_output_dir():
        if not os.path.exists(Config.OUTPUT_DIR):
            os.makedirs(Config.OUTPUT_DIR)

Config.ensure_output_dir()
