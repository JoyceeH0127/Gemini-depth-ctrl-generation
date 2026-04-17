
import io
from PIL import Image
from thermal_imaging_synthesis.config.config import VertexAIConfig
from vertex_ai_client import VertexAIClient


# ================= 配置 =================
IMAGE_1_PATH = "D:\\dataset\\dataset\\Gibson\\Collierville\\pano\\rgb\\point_p000001_view_equirectangular_domain_rgb.png"
IMAGE_2_PATH = "D:\\dataset\\dataset\\Gibson\\Collierville\\pano\\depth_vis\\point_p000001.png"
OUTPUT_PATH = "D:\\dataset\\dataset\\Gibson\\Collierville\\pano\\depth_ctrl\\output_panorama.png"


# ================= 工具函数 =================
def resize_image(path, size):
    img = Image.open(path).convert("RGB")
    return img.resize(size, Image.Resampling.LANCZOS)



# ================= Step 1 =================
def generate_scene_description(vertex_client, prompt):
    # 使用 VertexAIClient 的 analyze_image 方法
    return vertex_client.analyze_image(
        image_path=IMAGE_1_PATH,
        prompt=prompt,
        temperature=0.2,
        max_output_tokens=4096
    )



# ================= Step 2 =================
def generate_panorama(vertex_client, prompt):
    # 这里我们用 generate_thermal_image，传入 IMAGE_1_PATH 作为参考图像，prompt 作为描述
    images = vertex_client.generate_image(
        prompt=prompt,
        reference_image_path=IMAGE_1_PATH,
        output_path=OUTPUT_PATH,
        number_of_images=1,
        temperature=0.2  # 强制温度为0.2
    )
    if images:
        # 返回PIL Image对象
        return images[0]
    return None


# ================= 主流程 =================
def main():
    print("=== Step 1: Scene Analysis ===")

    # 初始化 VertexAIClient
    vertex_client = VertexAIClient()
    vertex_client.initialize()

    prompt_1 = """
    make a professional and concise description of the given scene, following the form: 
    Detailed Scene Description:
    The scene is a daytime urban street view under an overcast sky with soft, diffuse lighting.
    Foreground: A red brick sidewalk with a white metal guardrail running along the path.
    Midground: Lush green trees with detailed branches and leaves forming a canopy overhead. A red sedan is parked in a concrete parking space on the left. A grey asphalt road runs along the right side.
    Background: Modern commercial buildings and distant city elements visible through the foliage.
    """

    scene_desc = generate_scene_description(vertex_client, prompt_1)
    print(scene_desc)

    print("=== Step 2: Panorama Generation ===")

    prompt_2 = f"""
   Role & Objective:
    You are an expert 360-degree VR photographer and CGI artist. Generate a high-fidelity, photorealistic, seamless 360-degree equirectangular panorama image. The output must strictly adhere to the visual content of [Image 1] and the precise geometry structure of [Image 2].
    
    Reference Alignment Instructions:
    Layout & Geometry: Use [Image 2] (Depth Map) as the ground truth for scene depth and 3D structure. Maintain the exact position of the trees, the parking lot, cars, pedestrians and the road. Do not add or remove major objects.
    Visual Style: Use [Image 1] (RGB) as the reference for color palette, texture, and lighting conditions.
    
    Detailed Scene Description:
    {scene_desc}
    
    Output Quality Requirements:
    Format: Equirectangular projection (16:9 aspect ratio).
    Style: Photorealistic, 4k resolution, raw photography style, sharp focus, no motion blur.
    Constraint: Ensure the image is seamless at the edges for VR viewing.
    """


    img = generate_panorama(vertex_client, prompt_2)

    if img is None:
        print("Image generation failed.")
        return

    # 输出16:9尺寸，优先4K（3840x2160），如需兼容旧代码可用3840x1920
    # img = img.resize((3840, 1920), Image.Resampling.LANCZOS)
    img.save(OUTPUT_PATH)

    print(f"Saved to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
