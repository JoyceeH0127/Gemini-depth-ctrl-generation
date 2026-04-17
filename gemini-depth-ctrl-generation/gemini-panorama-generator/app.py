import gradio as gr
from PIL import Image
import os
import datetime
import base64
import io
from config import Config
from panorama_generator import PanoramaGenerator

# Initialize Generator
generator = None
try:
    generator = PanoramaGenerator()
except Exception as e:
    print(f"Warning: Could not initialize PanoramaGenerator: {e}")

def process_images(rgb_img, depth_img, mode, temperature, custom_prompt):
    if not generator:
        return None, "System not initialized correctly. Check API Key."
    
    if rgb_img is None or depth_img is None:
        return None, "Please upload both RGB and Depth images."

    status_log = f"Starting generation in mode: {mode} (Model: {Config.MODEL_NAME}) with Temperature: {temperature}...\n"
    
    # 1. Generate VR Panorama
    try:
        response = generator.generate_panorama(rgb_img, depth_img, temperature, custom_prompt)
        
        if response is None:
             print("Response is None.")
             return None, "Generation failed. Check console logs for errors."

        print("Generation request completed. Parsing response...")
        status_log += "Generation request completed. Parsing response...\n"
        
        generated_vr_pano = None
        
        # Try to extract image from response
        try:
            print(f"Response type: {type(response)}")
            # Debug: Inspect candidates
            if hasattr(response, 'candidates'):
                 print(f"Candidates count: {len(response.candidates)}")
                 if response.candidates:
                     print(f"First candidate parts: {len(response.candidates[0].content.parts)}")
            
            # Check for inline data
            if hasattr(response, 'candidates') and response.candidates:
                for part in response.candidates[0].content.parts:
                    if part.inline_data: # Image data
                        print("Found inline_data part.")
                        image_data = part.inline_data.data
                        image_bytes = base64.b64decode(image_data) if isinstance(image_data, str) else image_data
                        
                        generated_vr_pano = Image.open(io.BytesIO(image_bytes))
                        # Ensure 2:1 aspect ratio (Gemini API doesn't support "2:1" directly)
                        generated_vr_pano = generator._ensure_2to1_aspect_ratio(generated_vr_pano)
                        status_log += "Successfully extracted image from response parts.\n"
                        status_log += f"Image size after 2:1 adjustment: {generated_vr_pano.size[0]}x{generated_vr_pano.size[1]}\n"
                        print("Successfully extracted image.")
                        break
                    elif part.text:
                        print(f"Found text part: {part.text[:50]}...")
                        status_log += f"Model returned text: {part.text[:100]}...\n"
                        
            # Fallback for other structures (e.g. byte_content)
            if generated_vr_pano is None:
                 print("No inline_data found. Checking alternatives...")

            
            # Fallback/Alternative check structure (depending on SDK version)
            if generated_vr_pano is None and hasattr(response, 'text'):
                 status_log += f"Model response text: {response.text}\n"

        except Exception as parse_error:
            print(f"Error parsing response: {parse_error}")
            status_log += f"Error parsing response: {parse_error}\n"

        if generated_vr_pano is None:
             generated_vr_pano = rgb_img # Fallback to input if extraction fails so UI doesn't break
             status_log += "Warning: No image found in response. Showing input RGB as fallback.\n"
        
    except Exception as e:
        return None, f"Error: {str(e)}"

    # Auto-save the generated image
    try:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"pano_{timestamp}.png"
        save_path = os.path.join(Config.OUTPUT_DIR, filename)
        
        # Ensure directory exists (Config does this on import, but good to be safe)
        os.makedirs(Config.OUTPUT_DIR, exist_ok=True)
        
        generated_vr_pano.save(save_path)
        print(f"Saved generated panorama to: {save_path}")
        status_log += f"Saved to: {save_path}\n"
    except Exception as save_err:
        print(f"Error saving image: {save_err}")
        status_log += f"Warning: Failed to save to disk: {save_err}\n"

    # Return only the generated VR panorama
    return generated_vr_pano, status_log

with gr.Blocks(title="VR Panorama Synthesis System") as demo:
    gr.Markdown("# VR 360 Panorama Generation (Gemini-3-Pro)")
    gr.Markdown("Upload an RGB Visual Reference and a Depth Map to generate a photorealistic 360 panorama suitable for VR.")
    
    with gr.Row():
        with gr.Column():
            input_rgb = gr.Image(label="Visual Reference (RGB)", type="pil")
            input_depth = gr.Image(label="Structural Reference (Depth Map)", type="pil")
            
            with gr.Accordion("Advanced Settings", open=True):
                mode = gr.Dropdown(choices=["Standard", "High Fidelity", "Fast"], value="High Fidelity", label="Generation Mode (Reserved)")
                temperature = gr.Slider(minimum=0.0, maximum=1.0, value=0.4, step=0.1, label="Temperature (Creativity)")
                
                # Import default prompt
                from prompts import VR_Prompts
                system_prompt_input = gr.Textbox(
                    label="System Prompt (Detailed Instructions)", 
                    lines=10, 
                    value=VR_Prompts.SYSTEM_INSTRUCTION,
                    interactive=True
                )
            
            btn_generate = gr.Button("Generate Panorama", variant="primary")
        
        with gr.Column():
            output_log = gr.Textbox(label="Status Log")
            # Using Image component for VR view (Gradio 3.x+ often supports 360 viewer via specific extensions or just flat image)
            # For now, we display flat equirectangular image.
            output_vr = gr.Image(label="Generated VR Panorama (Equirectangular)", type="pil")
            
    btn_generate.click(
        process_images,
        inputs=[input_rgb, input_depth, mode, temperature, system_prompt_input],
        outputs=[output_vr, output_log]
    )

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7861)
