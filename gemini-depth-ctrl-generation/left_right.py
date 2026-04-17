import io
import os
import time
import random
from pathlib import Path
from PIL import Image
# from config_ir import VertexAIConfig
from vertex_ai_client_ir import VertexAIClient
from google.api_core.exceptions import TooManyRequests

# ================= 配置 =================
INPUT_DIR = "C:\\Users\\R11000\\Downloads\\synthetic-thermal-data-main\\synthetic-thermal-data-main\\ir\\test"
IMAGE_DIR = os.path.join(INPUT_DIR, "RGB")
OUTPUT_DIR = "C:\\Users\\R11000\\Downloads\\synthetic-thermal-data-main\\synthetic-thermal-data-main\\ir\\test_ir_output"
REFERENCE_DIR = os.path.join(os.path.dirname(__file__), "reference", "left_right")
os.makedirs(OUTPUT_DIR, exist_ok=True)

TARGET_SIZE = (1024, 1024)  # 生成输出尺寸

# ================= 工具函数 =================
def resize_image(img: Image.Image, size):
    return img.resize(size, Image.Resampling.LANCZOS)

def find_depth_file(rgb_file: str):
    base = rgb_file.split("_view_")[0]
    for ext in [".png", ".jpg", ".webp"]:
        # candidate = os.path.join(DEPTH_DIR, base + ext)
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

def get_reference_images(reference_dir: str):
    if not os.path.isdir(reference_dir):
        print(f"⚠️ Reference dir not found: {reference_dir}")
        return []
    return sorted([
        os.path.join(reference_dir, f)
        for f in os.listdir(reference_dir)
        if f.lower().endswith((".png", ".jpg", ".jpeg", ".webp"))
    ])


def generate_panorama_with_retry(vertex_client, prompt, image_path, output_path, reference_image_paths, retries=3):
    for attempt in range(retries):
        try:
            ordered_images = [image_path] + reference_image_paths
            images = vertex_client.generate_image(
                prompt=prompt,
                input_image_paths=ordered_images,
                output_path=output_path,
                number_of_images=1,
                temperature=0.4
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

    reference_images = get_reference_images(REFERENCE_DIR)
    if not reference_images:
        print("❌ No reference images found, abort.")
        return

    rgb_files = sorted([f for f in os.listdir(IMAGE_DIR) if f.lower().endswith((".png", ".jpg", ".webp"))])
    results = []

    for idx, rgb_file in enumerate(rgb_files):
        rgb_path = os.path.join(IMAGE_DIR, rgb_file)


        # Step 2: Panorama generation
        prompt_2 = f"""

        # Context
        I am providing multiple images to define a specific visual style and one target image to apply this style to.
        - **Reference Images[Image 2][Image 3][Image 4][Image 5]**: These are real-world photos taken with a special coated lens (Near-Infrared/False Color). 
        - **Target Image[Image 1]**: A standard RGB image. 

        # Task
        Analyze the **shared visual characteristics** across all Reference Images and transfer this specific "Lens Signature" to the Target Image. 

        # Step 1: Cross-Reference Analysis
        Please look at all Reference Images collectively and extract the invariant style rules:
        1. **Vegetation/Foliage**: Observe how green plants are rendered across different references. (Likely shifting to Sakura Pink, White, or Pale Red).
        2. **Inorganic Objects**: Observe how roads, buildings, and water are rendered. Do they retain their color, become desaturated, or shift to a specific hue (e.g., Cyan/Sepia)?
        3. **Lighting/Contrast**: Note the specific glow or contrast curve typical of this lens coating. 

        # Step 2: Semantic Style Transfer
        Apply these extracted rules to the Target Image:
        - Identify the vegetation in the Target Image and strictly apply the "Pink/White" shift observed in the references. 
        - **Crucial**: Do not simply blend the images. You must simulate the *physics* of the lens. If the references show that *only* living plants turn pink, then do not turn a green car pink in the Target Image.
        - Maintain the high-frequency details (edges, textures) of the Target Image. 

        # Output
        Generate the transformed Target Image that looks like it was part of the Reference Image set.
        """
        base_name = os.path.splitext(rgb_file)[0]
        output_file = os.path.join(OUTPUT_DIR, base_name + "_output_panorama.png")
        gen_img_path = generate_panorama_with_retry(
            vertex_client,
            prompt_2,
            rgb_path,
            output_file,
            reference_images
        )
        if gen_img_path is None:
            continue

        results.append({
            "rgb": rgb_path,
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
                # depth = Image.open(item["depth"]).resize((TARGET_SIZE[0]//2, TARGET_SIZE[1]//2), Image.Resampling.LANCZOS)
                gen = Image.open(item["gen"]).resize((TARGET_SIZE[0]//2, TARGET_SIZE[1]//2), Image.Resampling.LANCZOS)
                imgs.append((rgb, gen))
            except Exception as e:
                print(f"⚠️ Failed to open/resize images for merge: {e}")
                continue

        if not imgs:
            print("⚠️ No valid images to merge in this group, skipping")
            continue

        merged_w = imgs[0][0].width * 2
        merged_h = imgs[0][0].height * len(imgs)
        merged = Image.new("RGB", (merged_w, merged_h))
        for i, (rgb, gen) in enumerate(imgs):
            y = i * rgb.height
            merged.paste(rgb, (0, y))
            merged.paste(gen, (rgb.width*2, y))
        merged_path = os.path.join(OUTPUT_DIR, f"merged_{group_idx//10+1}.png")
        merged.save(merged_path)
        print(f"✅ Saved merged image: {merged_path}")

if __name__ == "__main__":
    main()
