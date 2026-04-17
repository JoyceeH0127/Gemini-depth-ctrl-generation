import io
import os
import time
import random
from pathlib import Path
from PIL import Image
# from thermal_imaging_synthesis.config.config import VertexAIConfig
from vertex_ai_client_sim import VertexAIClient
from google.api_core.exceptions import TooManyRequests

# ================= 配置 =================
# INPUT_DIR = "D:\\depth_ctrl\\sim_scenes\\sdg_gemini\\Autel_Garage_03_2026-01-22-17-51-52\\Autel_Garage_03_2026-01-22-17-51-52\\cube_head_left"
# INPUT_DIR = "D:\\depth_ctrl\\sim_scenes\\sdg_gemini\\Autel_Cathedral_Of_The_Dead_2026-01-22-17-34-19\\Autel_Cathedral_Of_The_Dead_2026-01-22-17-34-19\\cube_head_left"
# INPUT_DIR = "D:\\depth_ctrl\\sim_scenes\\sdg_gemini\\Autel_OperaAuditorium_m_2026-01-22-17-07-21\\Autel_OperaAuditorium_m_2026-01-22-17-07-21\\cube_head_left"
# INPUT_DIR = "D:\\depth_ctrl\\sim_scenes\\sdg_gemini\\Autel_UEWarehouseCar_2026-01-22-17-41-33\\Autel_UEWarehouseCar_2026-01-22-17-41-33\\cube_head_left"
# INPUT_DIR = "D:\\depth_ctrl\\sim_scenes\\sdg_gemini\\Autel_AIUE_V01_004_m_2026-01-22-17-21-24\\Autel_AIUE_V01_004_m_2026-01-22-17-21-24\\cube_head_left"
# INPUT_DIR = "D:\\depth_ctrl\\sim_scenes\\sdg_gemini\\Autel_ConcertHall_m_2026-01-22-17-11-45\\Autel_ConcertHall_m_2026-01-22-17-11-45\\cube_head_left"
INPUT_DIR = "D:\depth_ctrl\sim_scenes\sdg_gemini\Autel_High_School_Basketball_Gym_2026-01-22-17-03-36\cube_head_left"

IMAGE_DIR = os.path.join(INPUT_DIR, "CubeScene")
DEPTH_DIR = os.path.join(INPUT_DIR, "CubeDepth_vis")
OUTPUT_DIR = os.path.join(INPUT_DIR, "CubeOutputs_dirty")
os.makedirs(OUTPUT_DIR, exist_ok=True)

TARGET_SIZE = (2560, 5120)  # 生成输出尺寸

# ================= 工具函数 =================
def resize_image(img: Image.Image, size):
    return img.resize(size, Image.Resampling.LANCZOS)

def find_depth_file(rgb_file: str):
    base = rgb_file.split("_view_")[0]
    for ext in [".png", ".jpg", ".webp"]:
        candidate = os.path.join(DEPTH_DIR, base + ext)
        if os.path.exists(candidate):
            return candidate
    return None

def generate_with_retry(vertex_client, image_path, prompt, retries=5):
    for attempt in range(retries):
        try:
            return vertex_client.analyze_image(
                image_path=image_path,
                prompt=prompt,
                temperature=0.2,
                max_output_tokens=4096
            )
        except TooManyRequests:
            wait = (2 ** attempt) + random.random()
            print(f"⚠️ 429 TooManyRequests, retrying in {wait:.1f}s (attempt {attempt+1}/{retries})")
            time.sleep(wait)
        except Exception as e:
            print(f"⚠️ Error generating scene description: {e}")
            time.sleep(1)
    print("❌ Failed after retries")
    return None

def generate_panorama_with_retry(vertex_client, prompt, image_path, output_path, retries=3):
    for attempt in range(retries):
        try:
            images = vertex_client.generate_image(
                prompt=prompt,
                reference_image_path=image_path,
                output_path=output_path,
                number_of_images=1,
                temperature=0.2
            )
            if images:
                # Resize before save to TARGET_SIZE
                img = images[0].resize(TARGET_SIZE, Image.Resampling.LANCZOS)
                img.save(output_path)
                return output_path
        except TooManyRequests:
            wait = (2 ** attempt) + random.random()
            print(f"⚠️ 429 TooManyRequests during panorama generation, retry {attempt+1}/{retries}, wait {wait:.1f}s")
            time.sleep(wait)
        except Exception as e:
            print(f"⚠️ Error generating panorama: {e}")
            time.sleep(1)
    print(f"❌ Failed to generate panorama for {image_path}")
    return None

# ================= 主流程 =================
def main():
    print("=== Batch Folder Processing ===")

    vertex_client = VertexAIClient()
    vertex_client.initialize()

    rgb_files = sorted([f for f in os.listdir(IMAGE_DIR) if f.lower().endswith((".png", ".jpg", ".webp"))])
    results = []

    for idx, rgb_file in enumerate(rgb_files):
        rgb_path = os.path.join(IMAGE_DIR, rgb_file)
        base, _ = os.path.splitext(rgb_file)

        for ext in [".png", ".jpg", ".webp"]:
            depth_file = base + ext
            depth_path = os.path.join(DEPTH_DIR, depth_file)
            if os.path.exists(depth_path):
                break
        else:
            print(f"No depth for {rgb_file}, skip.")
            continue
        
        # # Step 1: Scene description
        # prompt_1 = """
        # make a professional and concise description of the given scene, following the form: 
        # Detailed Scene Description:
        # The scene is a daytime urban street view under an overcast sky with soft, diffuse lighting.
        # Foreground: A red brick sidewalk with a white metal guardrail running along the path.
        # Midground: Lush green trees with detailed branches and leaves forming a canopy overhead. A red sedan is parked in a concrete parking space on the left. A grey asphalt road runs along the right side.
        # Background: Modern commercial buildings and distant city elements visible through the foliage.
        # """
        # scene_desc = generate_with_retry(vertex_client, rgb_path, prompt_1)
        # if scene_desc is None:
        #     print(f"⚠️ Scene description failed for {rgb_file}, skipping")
        #     continue

        # Step 2: Panorama generation
        # dirty
        prompt_2 = f"""
        **Role & Objective:**
        You are an expert 360-degree VR photographer and CGI artist specializing in sim-to-real scene translation. Generate a high-fidelity, photorealistic, seamless 360-degree equirectangular panorama by transforming a simulated environment into a convincingly real-world scene. The output must strictly adhere to the visual content of [Image 1] and the precise geometry structure of [Image 2].
        
        **Reference Alignment Instructions:**
        *   **Layout & Geometry: Use [Image 2] (Depth Map) as the ground truth for scene depth and 3D structure. Maintain the exact position of the trees, the parking lot, cars, pedestrians, road outsides and windows, walls, roofs, furnitures, cabinets and other objects insides. ** Do not add or remove any objects.**
        *   **Visual Translation (Sim → Real):** Use [Image 1] (RGB) as the reference for overall color palette, scene semantics, and environment type, but replace all synthetic or CGI-like appearances with real-world visual characteristics, with a strong emphasis on **environmental pollution, aging, and surface contamination**.
            1. **Material Realism:** Convert artificial textures into realistic counterparts with appropriate weathering and imperfections. Replace clean, uniform surfaces with realistic material responses (physically plausible roughness, micro-normal variation, subtle reflectance changes under strong daylight), Lighting should serve to reveal surface dirt and pollution details clearly, not overpower them.
            2. **Surface Pollution & Dirt Accumulation (CRITICAL):** Apply realistic dirt, dust, soot, stains, and pollution marks to **ground surfaces (roads, sidewalks, parking lots)** and **wall surfaces (building walls, boundary walls, facades)**, Avoid uniform dirt patterns; contamination should appear irregular, layered, and consistent with long-term real-world exposure.
            3. **Usage Trace:** Introduce subtle signs of real-world usage without altering geometry, such as dirt, wear, and minor surface damage, ensuring these details respond naturally to environmental pollution and aging.
        
        **Detailed Scene Description:**
        Refer strictly to [Image 1] for the specific content.
        
        **Visual Fidelity Protocol (CRITICAL):**
        1.  **Object Inventory**: deeply analyze [Image 1] (RGB) to identify ALL foreground and midground objects (including but not limited to: vehicles, pedestrians, guardrails, trees, signs, buildings, windows, walls, roofs, furnitures, cabinets and other objects insides).
        2.  **Strict Preservation**: Every distinct object found in [Image 1] MUST appear in the generated panorama. **DO NOT REMOVE OR OMIT ANY OBJECTS.**
        3.  **Spatial Anchoring**: Use [Image 2] (Depth Map) to determine the exact 3D position of these objects.
        4.  **No Hallucinations**: Do not invent new major objects that contradict the scene logic, and do not erase existing ones.
    
        **Output Quality Requirements:**
        *   **Structure Consistency**: The output MUST align pixel-perfectly with key landmarks in the input.
        *   Format: Equirectangular projection (9:16 aspect ratio).
        *   Style: Photorealistic, 4k resolution, raw photography style, clear sunny daylight appearance, sharp focus, no motion blur.
        *   Constraint: Ensure the image is seamless at the edges.
        """

        # brighter
        # prompt_2 = f"""
        # **Role & Objective:**
        # You are an expert 360-degree VR photographer and CGI artist specializing in sim-to-real scene translation. Generate a high-fidelity, photorealistic, seamless 360-degree equirectangular panorama by transforming a simulated environment into a convincingly real-world scene. The output must strictly adhere to the visual content of [Image 1] and the precise geometry structure of [Image 2].
        
        # **Reference Alignment Instructions:**
        # *   **Layout & Geometry: Use [Image 2] (Depth Map) as the ground truth for scene depth and 3D structure. Maintain the exact position of the trees, the parking lot, cars, pedestrians, road outsides and windows, walls, roofs, furnitures and other objects insides. ** Do not add or remove any objects.**
        # *   **Visual Translation (Sim → Real):** Use [Image 1] (RGB) as the reference for overall color palette, scene semantics, and environment type, but replace all synthetic or CGI-like appearances with real-world visual characteristics, while simulating a **brighter, clear, sunny daytime lighting condition**.
        #     1. **Material Realism:** Convert artificial textures into realistic counterparts with appropriate weathering and imperfections. Replace clean, uniform surfaces with realistic material responses (physically plausible roughness, micro-normal variation, subtle reflectance changes under strong daylight).
        #     2. **Lighting Authenticity (Sunny Conditions):** Increase overall scene illumination to reflect a clear, sunny day. Introduce natural sunlight with higher intensity, crisp but realistic shadows, stronger highlights, and soft sky-fill ambient light. Ensure lighting remains physically consistent with object geometry and depth, without overexposure or loss of detail.
        #     3. **Usage Trace:** Introduce subtle signs of real-world usage without altering geometry, such as dirt, wear, and minor surface damage, ensuring these details respond naturally to brighter lighting conditions.
        
        # **Detailed Scene Description:**
        # Refer strictly to [Image 1] for the specific content.
        
        # **Visual Fidelity Protocol (CRITICAL):**
        # 1.  **Object Inventory**: deeply analyze [Image 1] (RGB) to identify ALL foreground and midground objects (including but not limited to: vehicles, pedestrians, guardrails, trees, signs, buildings, windows, walls, roofs, furnitures and other objects insides).
        # 2.  **Strict Preservation**: Every distinct object found in [Image 1] MUST appear in the generated panorama. **DO NOT REMOVE OR OMIT ANY OBJECTS.**
        # 3.  **Spatial Anchoring**: Use [Image 2] (Depth Map) to determine the exact 3D position of these objects.
        # 4.  **No Hallucinations**: Do not invent new major objects that contradict the scene logic, and do not erase existing ones.
    
        # **Output Quality Requirements:**
        # *   **Structure Consistency**: The output MUST align pixel-perfectly with key landmarks in the input.
        # *   Format: Equirectangular projection (9:16 aspect ratio).
        # *   Style: Photorealistic, 4k resolution, raw photography style, clear sunny daylight appearance, sharp focus, no motion blur.
        # *   Constraint: Ensure the image is seamless at the edges.
        # """
        
        base_name = os.path.splitext(rgb_file)[0]
        output_file = os.path.join(OUTPUT_DIR, base_name + "_output_panorama.png")
        gen_img_path = generate_panorama_with_retry(vertex_client, prompt_2, rgb_path, output_file)
        if gen_img_path is None:
            continue

        results.append({
            "rgb": rgb_path,
            "depth": depth_path,
            "gen": gen_img_path
        })
        print(f"✅ Processed {rgb_file}")

    # Merge every 10
    for group_idx in range(0, len(results), 10):
        group = results[group_idx:group_idx+10]
        if not group:
            continue

        imgs = []
        for item in group:
            try:
                rgb = Image.open(item["rgb"]).resize((TARGET_SIZE[0]//2, TARGET_SIZE[1]//2), Image.Resampling.LANCZOS)
                depth = Image.open(item["depth"]).resize((TARGET_SIZE[0]//2, TARGET_SIZE[1]//2), Image.Resampling.LANCZOS)
                gen = Image.open(item["gen"]).resize((TARGET_SIZE[0]//2, TARGET_SIZE[1]//2), Image.Resampling.LANCZOS)
                imgs.append((rgb, depth, gen))
            except Exception as e:
                print(f"⚠️ Failed to open/resize images for merge: {e}")
                continue

        if not imgs:
            print("⚠️ No valid images to merge in this group, skipping")
            continue

        merged_w = imgs[0][0].width * 3
        merged_h = imgs[0][0].height * len(imgs)
        merged = Image.new("RGB", (merged_w, merged_h))
        for i, (rgb, depth, gen) in enumerate(imgs):
            y = i * rgb.height
            merged.paste(rgb, (0, y))
            merged.paste(depth, (rgb.width, y))
            merged.paste(gen, (rgb.width*2, y))
        merged_path = os.path.join(OUTPUT_DIR, f"merged_{group_idx//10+1}.png")
        merged.save(merged_path)
        print(f"✅ Saved merged image: {merged_path}")

if __name__ == "__main__":
    main()
