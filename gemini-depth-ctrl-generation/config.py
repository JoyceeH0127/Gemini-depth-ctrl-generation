"""
Thermal Imaging Synthesis System Configuration
热成像合成系统配置文件
"""

import os
from pathlib import Path
from pydantic import BaseModel
from typing import Optional, Literal
from enum import Enum

# 自动加载 .env 文件（不依赖python-dotenv）
def _load_env_file():
    """手动解析并加载.env文件"""
    env_path = Path(__file__).parent.parent / '.env'
    if env_path.exists():
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                # 跳过空行和注释
                if not line or line.startswith('#'):
                    continue
                # 解析 KEY=VALUE 格式
                if '=' in line:
                    key, _, value = line.partition('=')
                    key = key.strip()
                    value = value.strip()
                    # 移除可能的引号
                    if value.startswith('"') and value.endswith('"'):
                        value = value[1:-1]
                    elif value.startswith("'") and value.endswith("'"):
                        value = value[1:-1]
                    # 只设置未设置的环境变量
                    if key and key not in os.environ:
                        os.environ[key] = value

_load_env_file()


def get_default_project_id() -> str:
    """
    从环境变量获取默认的Google Cloud Project ID
    
    优先级:
    1. GOOGLE_CLOUD_PROJECT
    2. GCLOUD_PROJECT
    3. GCP_PROJECT
    
    Returns:
        项目ID字符串
    """
    return os.environ.get("GOOGLE_CLOUD_PROJECT") or \
           os.environ.get("GCLOUD_PROJECT") or \
           os.environ.get("GCP_PROJECT") or \
           ""


# 默认项目ID
DEFAULT_PROJECT_ID = get_default_project_id()


class GeminiModel(str, Enum):
    """Available Gemini models for different tasks"""
    # 用于文本分析和特征提取（Gemini 3 Pro）
    GEMINI_PRO_PREVIEW = "gemini-3-pro-preview"
    # 用于图像生成（Gemini 3 Pro Image）
    GEMINI_IMAGE_PREVIEW = "gemini-3-pro-image-preview"
    # 用于多模态分析（图像理解）（Gemini 3 Pro）
    GEMINI_VISION = "gemini-3-pro-preview"


class VertexAIConfig(BaseModel):
    """Vertex AI Configuration"""
    project_id: str = DEFAULT_PROJECT_ID
    location: str = "global"  # 使用global区域
    
    # 模型选择配置
    analysis_model: str = GeminiModel.GEMINI_PRO_PREVIEW.value  # 用于分析
    generation_model: str = GeminiModel.GEMINI_IMAGE_PREVIEW.value  # 用于图像生成
    vision_model: str = GeminiModel.GEMINI_VISION.value  # 用于图像理解


class RAGConfig(BaseModel):
    """RAG Database Configuration"""
    # ChromaDB配置
    persist_directory: str = "./data/chroma_db"
    collection_name: str = "thermal_features"
    
    # 嵌入模型配置
    embedding_model: str = "all-MiniLM-L6-v2"
    
    # 检索配置
    top_k: int = 5
    similarity_threshold: float = 0.7


class ThermalFeatureConfig(BaseModel):
    """Thermal Feature Extraction Configuration"""
    # 支持的对象类别
    supported_categories: list[str] = [
        "building",      # 建筑物/楼房
        "tree",          # 树木/植被
        "road",          # 公路/道路
        "vehicle",       # 车辆
        "water",         # 水体
        "ground",        # 地面/土地
        "sky",           # 天空
        "person",        # 人
        "infrastructure", # 基础设施
        "agricultural",  # 农业区域
    ]
    
    # 热成像特征维度
    feature_dimensions: list[str] = [
        "temperature_pattern",      # 温度模式
        "thermal_contrast",         # 热对比度
        "heat_distribution",        # 热量分布
        "edge_characteristics",     # 边缘特征
        "texture_pattern",          # 纹理模式
        "color_mapping",           # 颜色映射（热成像伪彩色）
        "relative_brightness",      # 相对亮度
        "temporal_variation",       # 时间变化特征
    ]


class ImageGenerationConfig(BaseModel):
    """Image Generation Configuration"""
    # 输出图像配置
    output_width: int = 3840
    output_height: int = 2160
    output_format: str = "png"
    
    # 生成参数
    temperature: float = 0.2
    top_p: float = 0.95
    max_output_tokens: int = 2048
    seed: int = 42
    
    # 重试配置
    max_retries: int = 3
    retry_delay: float = 1.0


class SystemConfig(BaseModel):
    """Main System Configuration"""
    vertex_ai: VertexAIConfig = VertexAIConfig()
    rag: RAGConfig = RAGConfig()
    thermal_feature: ThermalFeatureConfig = ThermalFeatureConfig()
    image_generation: ImageGenerationConfig = ImageGenerationConfig()
    
    # 数据路径
    data_dir: str = "./day2ir"
    output_dir: str = "./output"
    feature_db_path: str = "./data/thermal_features.json"
    
    # 日志配置
    log_level: str = "INFO"
    enable_verbose: bool = True


# 默认配置实例
DEFAULT_CONFIG = SystemConfig()


def load_config(config_path: Optional[str] = None) -> SystemConfig:
    """
    Load configuration from file or return default config
    
    Args:
        config_path: Path to configuration file (JSON)
        
    Returns:
        SystemConfig instance
    """
    import json
    from pathlib import Path
    
    if config_path and Path(config_path).exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
            return SystemConfig(**config_data)
    
    return DEFAULT_CONFIG


def save_config(config: SystemConfig, config_path: str) -> None:
    """
    Save configuration to file
    
    Args:
        config: SystemConfig instance
        config_path: Path to save configuration
    """
    import json
    from pathlib import Path
    
    Path(config_path).parent.mkdir(parents=True, exist_ok=True)
    
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config.model_dump(), f, indent=2, ensure_ascii=False)
