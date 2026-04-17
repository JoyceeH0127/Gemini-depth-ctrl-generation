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
BASE_DIR = r"D:\depth_ctrl\sim_scenes\sdg_gemini\gemini_0127\output\sdg_erp"
TARGET_SIZE = (2560, 5120)  # 生成输出尺寸

# ================= 工具函数 =================
def resize_image(img: Image.Image, size):
    return img.resize(size, Image.Resampling.LANCZOS)

def find_depth_file(rgb_file: str, depth_dir: str):
    base = rgb_file.split("_view_")[0]
    for ext in [".png", ".jpg", ".webp"]:
        candidate = os.path.join(depth_dir, base + ext)
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
def find_input_dirs(base_dir, prefix="Autel", sub_dir="cube_head_left"):
    input_dirs = []
    for name in os.listdir(base_dir):
        root = os.path.join(base_dir, name)
        if not os.path.isdir(root):
            continue
        if not name.startswith(prefix):
            continue
        candidate = os.path.join(root, sub_dir)
        if os.path.isdir(candidate):
            input_dirs.append(candidate)
    return input_dirs


def process_one_folder(input_dir, vertex_client):
    image_dir = os.path.join(input_dir, "CubeScene")
    depth_dir = os.path.join(input_dir, "CubeDepth_vis")
    output_dir = os.path.join(input_dir, "CubeOutputs_sunset")
    os.makedirs(output_dir, exist_ok=True)

    rgb_files = sorted([f for f in os.listdir(image_dir) if f.lower().endswith((".png", ".jpg", ".webp"))])
    results = []

    for idx, rgb_file in enumerate(rgb_files):
        rgb_path = os.path.join(image_dir, rgb_file)
        base, _ = os.path.splitext(rgb_file)

        for ext in [".png", ".jpg", ".webp"]:
            depth_file = base + ext
            depth_path = os.path.join(depth_dir, depth_file)
            if os.path.exists(depth_path):
                break
        else:
            print(f"No depth for {rgb_file}, skip.")
            continue

        # Step 2: Panorama generation
        # # cloudy
        # prompt_2 = f"""
        # # Role & Objective:
        # You are an expert 360-degree VR photographer and CGI artist. Generate a high-fidelity, photorealistic, seamless 360-degree equirectangular panorama image. The output must strictly adhere to the visual content of [Image 1] and the precise geometry structure of [Image 2], while altering the weather conditions.

        # **Reference Alignment Instructions:**
        # *   **Layout & Geometry:** Use [Image 2] (Depth Map) as the ground truth for scene depth and 3D structure. Maintain the exact position of the trees, the parking lot, cars, pedestrians and the road. Do not add or remove any objects.
        # *   **Visual Style:** Use [Image 1] (RGB) as the reference for object textures and local colors, but **shift the lighting and atmosphere to match a rainy day**. Reduce contrast and saturation slightly to mimic overcast lighting.
        
        # **Detailed Scene Description:**
        # Refer strictly to [Image 1] for the specific content, but transfer into a cloudy weather condition.

        # **Visual Fidelity Protocol (CRITICAL):**
        # 1.  **Object Inventory**: deeply analyze [Image 1] (RGB) to identify ALL foreground and midground objects (including but not limited to: vehicles, pedestrians, guardrails, trees, signs, and building facades).
        # 2.  **Strict Preservation**: Every distinct object found in [Image 1] MUST appear in the generated panorama. **DO NOT REMOVE OR OMIT ANY OBJECTS.**
        # 3.  **Spatial Anchoring**: Use [Image 2] (Depth Map) to determine the exact 3D position of these objects.
        # 4.  **No Hallucinations**: Do not invent new major objects that contradict the scene logic, and do not erase existing ones.

        # **Output Quality Requirements:**
        # *   **Structure Consistency**: The output MUST align pixel-perfectly with key landmarks in the input.
        # *   Format: Equirectangular projection (16:9 aspect ratio).
        # *   Style: Photorealistic, 4k resolution, raw photography style, sharp focus, no motion blur.
        # *   Constraint: Ensure the image is seamless at the edges.
        # """
        # dirty
        # prompt_2 = f"""
        # **Role & Objective:**
        # You are an expert 360-degree VR photographer and CGI artist specializing in sim-to-real scene translation. Generate a high-fidelity, photorealistic, seamless 360-degree equirectangular panorama by transforming a simulated environment into a convincingly real-world scene. The output must strictly adhere to the visual content of [Image 1] and the precise geometry structure of [Image 2].
        
        # **Reference Alignment Instructions:**
        # *   **Layout & Geometry: Use [Image 2] (Depth Map) as the ground truth for scene depth and 3D structure. Maintain the exact position of the trees, the parking lot, cars, pedestrians, road outsides and windows, walls, roofs, furnitures, cabinets and other objects insides. ** Do not add or remove any objects.**
        # *   **Visual Translation (Sim → Real):** Use [Image 1] (RGB) as the reference for overall color palette, scene semantics, and environment type, but replace all synthetic or CGI-like appearances with real-world visual characteristics, with a strong emphasis on **environmental pollution, aging, and surface contamination**.
        #     1. **Material Realism:** Convert artificial textures into realistic counterparts with appropriate weathering and imperfections. Replace clean, uniform surfaces with realistic material responses (physically plausible roughness, micro-normal variation, subtle reflectance changes under strong daylight), Lighting should serve to reveal surface dirt and pollution details clearly, not overpower them.
        #     2. **Surface Pollution & Dirt Accumulation (CRITICAL):** Apply realistic dirt, dust, soot, stains, and pollution marks to **ground surfaces (roads, sidewalks, parking lots)** and **wall surfaces (building walls, boundary walls, facades)**, Avoid uniform dirt patterns; contamination should appear irregular, layered, and consistent with long-term real-world exposure.
        #     3. **Usage Trace:** Introduce subtle signs of real-world usage without altering geometry, such as dirt, wear, and minor surface damage, ensuring these details respond naturally to environmental pollution and aging.
        
        # **Detailed Scene Description:**
        # Refer strictly to [Image 1] for the specific content.
        
        # **Visual Fidelity Protocol (CRITICAL):**
        # 1.  **Object Inventory**: deeply analyze [Image 1] (RGB) to identify ALL foreground and midground objects (including but not limited to: vehicles, pedestrians, guardrails, trees, signs, buildings, windows, walls, roofs, furnitures, cabinets and other objects insides).
        # 2.  **Strict Preservation**: Every distinct object found in [Image 1] MUST appear in the generated panorama. **DO NOT REMOVE OR OMIT ANY OBJECTS.**
        # 3.  **Spatial Anchoring**: Use [Image 2] (Depth Map) to determine the exact 3D position of these objects.
        # 4.  **No Hallucinations**: Do not invent new major objects that contradict the scene logic, and do not erase existing ones.
    
        # **Output Quality Requirements:**
        # *   **Structure Consistency**: The output MUST align pixel-perfectly with key landmarks in the input.
        # *   Format: Equirectangular projection (9:16 aspect ratio).
        # *   Style: Photorealistic, 4k resolution, raw photography style, clear sunny daylight appearance, sharp focus, no motion blur.
        # *   Constraint: Ensure the image is seamless at the edges.
        # """

        # # brighter
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

        # sunset
        prompt_2 = f"""
        # Role & Objective:
        You are an expert 360-degree VR photographer and CGI artist. Generate a high-fidelity, photorealistic, seamless 360-degree equirectangular panorama image. The output must strictly adhere to the visual content of [Image 1] and the precise geometry structure of [Image 2], , while altering the time-of-day and lighting conditions to sunset.

        **Reference Alignment Instructions:**
        *   **Layout & Geometry:** Use [Image 2] (Depth Map) as the ground truth for scene depth and 3D structure. Maintain the exact position of the trees, the parking lot, cars, pedestrians and the road. Do not add or remove any objects.
        *   **Visual Style:** Use [Image 1] (RGB) as the reference for object textures and local colors, but **shift the global illumination and atmosphere to a sunset scenario**. Introduce warm golden-hour lighting with soft orange and pink tones, long and directional shadows, and gentle highlights. Slightly enhance contrast and warmth while preserving realistic color balance.
        
        **Detailed Scene Description:**
        Refer strictly to [Image 1] for the specific content, but transfer the overall lighting and ambience to a natural sunset environment.

        **Visual Fidelity Protocol (CRITICAL):**
        1.  **Object Inventory**: deeply analyze [Image 1] (RGB) to identify ALL foreground and midground objects (including but not limited to: vehicles, pedestrians, guardrails, trees, signs, and building facades).
        2.  **Strict Preservation**: Every distinct object found in [Image 1] MUST appear in the generated panorama. **DO NOT REMOVE OR OMIT ANY OBJECTS.**
        3.  **Spatial Anchoring**: Use [Image 2] (Depth Map) to determine the exact 3D position of these objects.
        4.  **No Hallucinations**: Do not invent new major objects that contradict the scene logic, and do not erase existing ones.

        **Output Quality Requirements:**
        *   **Structure Consistency**: The output MUST align pixel-perfectly with key landmarks in the input.
        *   Format: Equirectangular projection (16:9 aspect ratio).
        *   Style: Photorealistic, 4k resolution, raw photography style, sharp focus, no motion blur.
        *   Constraint: Ensure the image is seamless at the edges.
        """
        
        base_name = os.path.splitext(rgb_file)[0]
        output_file = os.path.join(output_dir, base_name + "_output_panorama.png")
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
        merged_path = os.path.join(output_dir, f"merged_{group_idx//10+1}.png")
        merged.save(merged_path)
        print(f"✅ Saved merged image: {merged_path}")


def main():
    print("=== Batch Folder Processing ===")

    vertex_client = VertexAIClient()
    vertex_client.initialize()

    input_dirs = find_input_dirs(BASE_DIR)
    print(f"📦 找到 {len(input_dirs)} 个输入目录")

    for input_dir in input_dirs:
        print(f"📂 Processing: {input_dir}")
        process_one_folder(input_dir, vertex_client)

if __name__ == "__main__":
    main()
