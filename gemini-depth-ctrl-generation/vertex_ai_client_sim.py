"""
Vertex AI Client for Gemini Models
使用Vertex AI调用Gemini模型的客户端
"""

import base64
import json
import logging
from pathlib import Path
from typing import Optional, Union, List, Dict, Any
from PIL import Image
import io
from google.genai import types

import vertexai
from vertexai.generative_models import GenerativeModel, Part, Image as VertexImage

from config_sim import VertexAIConfig, GeminiModel


logger = logging.getLogger(__name__)
INPUT_SIZE =(768, 1376)  #(2048, 1024) (3840, 1920)
TARGET_SIZE =(2560, 5120)  #(2048, 1024) (3840, 1920) 
class VertexAIClient:
    """
    Vertex AI Client for interacting with Gemini models
    支持Gemini Pro Preview（文本分析）和Gemini Image Preview（图像生成）
    """
    
    def __init__(self, config: Optional[VertexAIConfig] = None):
        """
        Initialize Vertex AI Client
        
        Args:
            config: Vertex AI configuration
        """
        self.config = config or VertexAIConfig()
        self._initialized = False
        self._analysis_model = None
        self._vision_model = None
        self._image_generation_model = None
        
    def initialize(self, project_id: Optional[str] = None):
        """
        Initialize Vertex AI with project settings
        
        Args:
            project_id: Google Cloud project ID (overrides config)
        """
        if self._initialized:
            return
            
        project = project_id or self.config.project_id
        location = self.config.location
        
        logger.info(f"Initializing Vertex AI with project={project}, location={location}")
        
        vertexai.init(project=project, location=location)
        self._initialized = True
        
    def _get_analysis_model(self) -> GenerativeModel:
        """Get or create analysis model instance"""
        if not self._initialized:
            self.initialize()
            
        if self._analysis_model is None:
            self._analysis_model = GenerativeModel(self.config.analysis_model)
            logger.info(f"Loaded analysis model: {self.config.analysis_model}")
            
        return self._analysis_model
    
    def _get_vision_model(self) -> GenerativeModel:
        """Get or create vision model instance for image understanding"""
        if not self._initialized:
            self.initialize()
            
        if self._vision_model is None:
            self._vision_model = GenerativeModel(self.config.vision_model)
            logger.info(f"Loaded vision model: {self.config.vision_model}")
            
        return self._vision_model
    
    def _get_image_generation_model(self) -> GenerativeModel:
        """Get or create image generation model instance (Gemini 3 Pro Image)"""
        if not self._initialized:
            self.initialize()
            
        if self._image_generation_model is None:
            self._image_generation_model = GenerativeModel(self.config.generation_model)
            logger.info(f"Loaded image generation model: {self.config.generation_model}")
            
        return self._image_generation_model
    
    def _load_image_orig(self, image_path: Union[str, Path]) -> Part:
        """
        Load image from file path and convert to Vertex AI Part
        
        Args:
            image_path: Path to image file
            
        Returns:
            Vertex AI Part object containing image
        """
        image_path = Path(image_path)
        
        if not image_path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")
        
        # Read image and encode to base64
        with open(image_path, "rb") as f:
            image_data = f.read()
        
        # Determine MIME type
        suffix = image_path.suffix.lower()
        mime_types = {
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".gif": "image/gif",
            ".webp": "image/webp",
        }
        mime_type = mime_types.get(suffix, "image/png")
        
        return Part.from_data(image_data, mime_type=mime_type)

    def _load_image(self, image_path: Union[str, Path]) -> Part:
        """
        Load image from file path and convert to Vertex AI Part
        
        Args:
            image_path: Path to image file
            
        Returns:
            Vertex AI Part object containing image
        """
        image_path = Path(image_path)
        
        if not image_path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")
        
        # Read image and encode to base64
        # with open(image_path, "rb") as f:
        #     image_data = f.read()
        image = Image.open(image_path).convert("RGB")
        image = image.resize(INPUT_SIZE, Image.BILINEAR)
        # Determine MIME type
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        image_data = buffer.getvalue()

        mime_type = "image/png"
        
        return Part.from_data(image_data, mime_type=mime_type)
     
    def analyze_text(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_output_tokens: int = 2048,
    ) -> str:
        """
        Analyze text using Gemini Pro Preview
        使用Gemini Pro Preview进行文本分析
        
        Args:
            prompt: Text prompt for analysis
            temperature: Sampling temperature
            max_output_tokens: Maximum output tokens
            
        Returns:
            Generated text response
        """
        model = self._get_analysis_model()
        
        generation_config = {
            "temperature": temperature,
            "max_output_tokens": max_output_tokens,
            "top_p": 0.95,
        }
        
        response = model.generate_content(
            prompt,
            generation_config=generation_config,
        )
        
        return response.text
    
    def analyze_image(
        self,
        image_path: Union[str, Path],
        prompt: str,
        temperature: float = 0.7,
        max_output_tokens: int = 16384,
    ) -> str:
        """
        Analyze image using Gemini Vision model
        使用Gemini Vision模型分析图像
        
        Args:
            image_path: Path to image file
            prompt: Analysis prompt
            temperature: Sampling temperature
            max_output_tokens: Maximum output tokens
            
        Returns:
            Analysis result as text
        """
        model = self._get_vision_model()
        
        # Load image
        image_part = self._load_image(image_path) # Resize to max allowed resolution
        
        generation_config = {
            "temperature": temperature,
            "max_output_tokens": max_output_tokens,
            "top_p": 0.95,
        }
        
        response = model.generate_content(
            [image_part, prompt],
            generation_config=generation_config,
        )
        
        return response.text
    
    def generate_image(
        self,
        prompt: str,
        reference_image_path: Optional[Union[str, Path]] = None,
        output_path: Optional[Union[str, Path]] = None,
        number_of_images: int = 1,
        temperature: float = 0.2,
    ) -> List[Image.Image]:
        """
        Generate image using Gemini 3 Pro Image model
        使用Gemini 3 Pro Image模型生成图像
        
        Args:
            prompt: Generation prompt describing the image
            reference_image_path: Optional reference image for style guidance
            output_path: Optional path to save generated image
            number_of_images: Number of images to generate
            temperature: Sampling temperature
        Returns:
            List of generated PIL Image objects
        """
        model = self._get_image_generation_model()
        
        # 使用正确的generation_config，不使用response_modalities
        # Gemini 3 Pro Image Preview会自动返回图像
        generation_config = {
            "temperature": temperature,
            "top_p": 0.95,
            "max_output_tokens": 32768,
            "image_config": {
                "aspect_ratio": "9:16",
            },
        }
        
        images = []
        
        for idx in range(number_of_images):
            content = []
            if reference_image_path:
                ref_image_part = self._load_image(reference_image_path)
                content.append(ref_image_part)
            content.append(prompt)
            
            try:
                response = model.generate_content(
                    content,
                    generation_config=generation_config,
                )
                
                # Extract image from response - handle different response formats
                image_found = False
                if response.candidates:
                    candidate = response.candidates[0]
                    if hasattr(candidate, 'content') and candidate.content:
                        parts = candidate.content.parts
                        for part in parts:
                            # Try different ways to get image data
                            if hasattr(part, 'inline_data') and part.inline_data:
                                try:
                                    image_data = part.inline_data.data
                                    if isinstance(image_data, str):
                                        # Base64 encoded
                                        image_data = base64.b64decode(image_data)
                                    pil_image = Image.open(io.BytesIO(image_data))
                                    pil_image = pil_image.resize(TARGET_SIZE, Image.Resampling.LANCZOS)
                                    images.append(pil_image)
                                    image_found = True
                                    
                                    # Save if output path is provided
                                    if output_path:
                                        save_path = Path(output_path)
                                        if number_of_images > 1:
                                            save_path = save_path.parent / f"{save_path.stem}_{idx}{save_path.suffix}"
                                        save_path.parent.mkdir(parents=True, exist_ok=True)
                                        pil_image = pil_image.resize(TARGET_SIZE, Image.Resampling.LANCZOS)
                                        pil_image.save(save_path)
                                        logger.info(f"Saved generated image to: {save_path}")
                                    break
                                except Exception as e:
                                    logger.error(f"Error decoding inline_data: {e}")
                            
                            # Try 'image' attribute (for different Gemini versions)
                            elif hasattr(part, 'image') and part.image:
                                try:
                                    if hasattr(part.image, 'data'):
                                        image_data = part.image.data
                                        if isinstance(image_data, str):
                                            image_data = base64.b64decode(image_data)
                                        pil_image = Image.open(io.BytesIO(image_data))
                                        pil_image = pil_image.resize(TARGET_SIZE, Image.Resampling.LANCZOS)
                                        images.append(pil_image)
                                        image_found = True
                                        
                                        if output_path:
                                            save_path = Path(output_path)
                                            if number_of_images > 1:
                                                save_path = save_path.parent / f"{save_path.stem}_{idx}{save_path.suffix}"
                                            save_path.parent.mkdir(parents=True, exist_ok=True)
                                            pil_image = pil_image.resize(TARGET_SIZE, Image.Resampling.LANCZOS)
                                            pil_image.save(save_path)
                                            logger.info(f"Saved generated image to: {save_path}")
                                        break
                                except Exception as e:
                                    logger.error(f"Error decoding image attribute: {e}")
                            
                            # Try file_data for some model versions
                            elif hasattr(part, 'file_data') and part.file_data:
                                try:
                                    file_uri = part.file_data.file_uri
                                    logger.info(f"Image available at file URI: {file_uri}")
                                    # Note: file URIs may need special handling
                                except Exception as e:
                                    logger.error(f"Error with file_data: {e}")
                
                if not image_found:
                    # Log response structure for debugging
                    logger.warning(f"No image found in response. Response structure: {type(response)}")
                    if response.candidates:
                        candidate = response.candidates[0]
                        logger.warning(f"Candidate content type: {type(candidate.content) if hasattr(candidate, 'content') else 'N/A'}")
                        if hasattr(candidate, 'content') and candidate.content:
                            for i, part in enumerate(candidate.content.parts):
                                logger.warning(f"Part {i} type: {type(part)}, attrs: {dir(part)}")
                                if hasattr(part, 'text') and part.text:
                                    logger.warning(f"Part {i} has text response: {part.text[:200]}...")
                            
            except Exception as e:
                logger.error(f"Error generating image {idx}: {e}")
                import traceback
                logger.error(traceback.format_exc())
                continue
        
        if not images:
            raise RuntimeError("Failed to generate any images")
        
        return images
    
    def generate_image_with_edit(
        self,
        base_image_path: Union[str, Path],
        prompt: str,
        output_path: Optional[Union[str, Path]] = None,
    ) -> Image.Image:
        """
        Edit/transform an existing image based on prompt using Gemini 3 Pro Image
        使用Gemini 3 Pro Image基于提示编辑/转换现有图像
        
        Args:
            base_image_path: Path to base image
            prompt: Edit prompt
            output_path: Optional path to save result
            
        Returns:
            Edited PIL Image
        """
        model = self._get_image_generation_model()
        
        # Load base image
        base_image_part = self._load_image(base_image_path)
        
        generation_config = {
            "temperature": 0.7,
            "top_p": 0.95,
            "max_output_tokens": 8192,
        }
        
        content = [
            "Base image to transform:",
            base_image_part,
            f"Transform this image according to: {prompt}",
        ]
        
        response = model.generate_content(
            content,
            generation_config=generation_config,
        )
        
        # Extract image from response
        result_image = None
        if response.candidates:
            for part in response.candidates[0].content.parts:
                if hasattr(part, 'inline_data') and part.inline_data:
                    image_data = part.inline_data.data
                    result_image = Image.open(io.BytesIO(image_data))
                    break
        
        if result_image is None:
            raise RuntimeError("Failed to generate edited image")
        
        if output_path:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            result_image.save(output_path)
            logger.info(f"Saved edited image to: {output_path}")
        
        return result_image
    
    def batch_analyze_images(
        self,
        image_pairs: List[Dict[str, str]],
        prompt: str,
    ) -> List[Dict[str, Any]]:
        """
        Batch analyze multiple image pairs
        批量分析多个图像对
        
        Args:
            image_pairs: List of dicts with 'rgb' and 'thermal' keys
            prompt: Analysis prompt
            
        Returns:
            List of analysis results
        """
        results = []
        
        for pair in image_pairs:
            try:
                analysis = self.analyze_image_pair(
                    rgb_image_path=pair['rgb'],
                    thermal_image_path=pair['thermal'],
                    prompt=prompt,
                )
                results.append({
                    "rgb_path": pair['rgb'],
                    "thermal_path": pair['thermal'],
                    "analysis": analysis,
                    "success": True,
                })
            except Exception as e:
                logger.error(f"Error analyzing pair {pair}: {e}")
                results.append({
                    "rgb_path": pair['rgb'],
                    "thermal_path": pair['thermal'],
                    "error": str(e),
                    "success": False,
                })
        
        return results


# Convenience function to create client
def create_vertex_client(
    project_id: Optional[str] = None,
    location: str = "global",
) -> VertexAIClient:
    """
    Create and initialize a Vertex AI client
    
    Args:
        project_id: Google Cloud project ID
        location: Vertex AI location (default: global)
        
    Returns:
        Initialized VertexAIClient
    """
    from config.config import DEFAULT_PROJECT_ID
    
    config = VertexAIConfig(
        project_id=project_id or DEFAULT_PROJECT_ID,
        location=location,
    )
    
    client = VertexAIClient(config)
    client.initialize(project_id)
    
    return client
