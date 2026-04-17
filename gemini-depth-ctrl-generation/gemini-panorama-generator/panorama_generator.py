import os
import io
import base64
from PIL import Image
from google import genai
from google.genai import types

try:
    from config import Config
    from prompts import VR_Prompts
except ImportError:
    # Fallback for standalone execution
    import sys
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from config import Config
    from prompts import VR_Prompts

class PanoramaGenerator:
    def __init__(self):
        self.client = self._init_client()
        self.model_name = Config.get_model_name()

    def _init_client(self):
        api_key = Config.GEMINI_API_KEY
        if api_key:
            return genai.Client(api_key=api_key)
        
        project_id = Config.PROJECT_ID
        location = Config.LOCATION
        if project_id and location:
            return genai.Client(vertexai=True, project=project_id, location=location)
        
        raise ValueError("No valid API Key or Google Cloud Project configuration found.")

    def _prepare_image_part(self, image: Image.Image, mime_type="image/jpeg"):
        byte_arr = io.BytesIO()
        image.save(byte_arr, format=mime_type.split('/')[-1].upper())
        return types.Part.from_bytes(data=byte_arr.getvalue(), mime_type=mime_type)

    def generate_panorama(self, rgb_image: Image.Image, depth_image: Image.Image, temperature: float = 0.4, custom_prompt: str = None):
        """
        Generates a 360 VR Panorama using Gemini.
        """
        print(f"Generating VR Panorama using {self.model_name} with temperature {temperature}...")
        
        # Use custom prompt if provided, otherwise fallback to default
        final_prompt = custom_prompt if custom_prompt else VR_Prompts.SYSTEM_INSTRUCTION
        
        contents = [
            types.Content(
                role="user",
                parts=[
                    types.Part.from_text(text=final_prompt),
                    types.Part.from_text(text=VR_Prompts.GENERATE_VR_PANORAMA),
                    types.Part.from_text(text="[Image 1] (Visual Reference - RGB)"),
                    self._prepare_image_part(rgb_image),
                    types.Part.from_text(text="[Image 2] (Structural Reference - Depth Map)"),
                    self._prepare_image_part(depth_image)
                ]
            )
        ]

        # Simplified for standard Gemini usage:
        try:
            print(f"Sending request to model: {self.model_name}...")
            # Using generate_content for Multimodal input
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=contents,
                config=types.GenerateContentConfig(temperature=temperature)
            )
            print("Response received from model.")
            # Debugging: Print available attributes/keys in response
            try:
                print(f"Response candidates: {response.candidates}")
            except:
                print(f"Response raw: {response}")
            return response
        except Exception as e:
            print(f"Error during generation: {e}")
            import traceback
            traceback.print_exc()
            return None

    def create_cinematic_shots(self, panorama_image: Image.Image):
        """
        Generates 4K crops/variations from the panorama.
        This conceptually is another model call or a post-processing step.
        """
        # Placeholder for 2nd stage generation
        pass
