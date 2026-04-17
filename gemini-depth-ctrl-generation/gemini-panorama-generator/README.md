# gemini-panorama-generator

# VR 360 Panorama Generation System (Gemini-3-Pro)

Based on Google Deepmind's **Gemini-3-Pro (Preview)** model, this system generates high-fidelity, photorealistic 360-degree equirectangular panoramas suitable for VR environments. It uses a dual-reference approach, combining an **RGB Visual Reference** (for style/texture) and a **Depth Map** (for structure/geometry) to ensure precise and consistent scene generation.

## key Features

*   **Dual-Reference Generation**:
    *   **Visual Reference (RGB)**: Defines color palette, lighting, and texture.
    *   **Structural Reference (Depth Map)**: Strictly controls scene geometry and object placement.
*   **High-Fidelity Output**: Generates 4K-ready equirectangular images (2:1 aspect ratio).
*   **Precision Controls**:
    *   **Temperature Slider (0.0 - 1.0)**: Adjust "Creativity" vs. "Fidelity". Lower values (<0.2) enforce strict adherence to the input structure; higher values (>0.7) add more detail.
    *   **Editable System Prompt**: Modify the core generation instructions directly in the UI to fine-tune results without restarting the server.
*   **Auto-Save**: All generated panoramas are automatically saved to the `outputs/` directory with timestamps.
*   **Seamless Loop**: Optimized prompts ensure the left and right edges of the panorama align perfectly for 360 viewing.

## Prerequisites

*   **Python 3.10+**
*   **Google Cloud Project**:
    *   Enabled **Vertex AI API**.
    *   Access to `gemini-3-pro-image-preview` model (ensure region availability, e.g., `global` or `us-central1`).
*   **Google Cloud CLI (gcloud)** (Optional but recommended for authentication).

## Installation

1.  **Clone/Navigate to directory**:
    ```bash
    cd path/to/project
    ```

2.  **Create Virtual Environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # Mac/Linux
    # venv\Scripts\activate   # Windows
    ```

3.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

## Configuration

1.  **Environment Setup**:
    Create a `.env` file or modify `config.py`. The system prioritizes `.env`.

    ```env
    # .env example
    PROJECT_ID=your-google-cloud-project-id
    LOCATION=global  # Important: Use 'global' if specific regions give 404
    GEMINI_API_KEY=  # Optional: Use if calling Gemini API directly instead of Vertex
    ```

2.  **Model Configuration**:
    Default settings in `config.py`:
    *   `MODEL_NAME`: `gemini-3-pro-image-preview`
    *   `OUTPUT_DIR`: `outputs`

## Usage

1.  **Start the Web UI**:
    ```bash
    gcloud auth application-default login
    gcloud config set project your-google-cloud-project-id
    ./venv/bin/python app.py
    ```

2.  **Access Interface**:
    Open your browser and navigate to: http://localhost:7861

3.  **Optimize Generation**:
    *   Upload **RGB Image** and **Depth Map**.
    *   Set **Temperature** (Recommended: `0.3` - `0.4` for balance).
    *   Expand **Advanced Settings** to tweak the System Prompt if needed (e.g., specific instructions like "Preserve red car").
    *   Click **Generate Panorama**.
    *   Check the `outputs/` folder for the saved high-res result.

## Troubleshooting

*   **404 Not Found Concept / Model**:
    *   Most likely due to incorrect `LOCATION`. Try changing `LOCATION` in `.env` or `config.py` to `global` or `us-central1`.
    *   Use `python tools/diagnose_model.py` to test model connectivity and find the correct model name format.
    *   Use `python tools/diagnose_model.py` to test model connectivity and find the correct model name format.
    *   Use `python tools/diagnose_model.py` to test model connectivity and find the correct model name format.
*   **Response Generation Failed**:
    *   Check the console logs. Detailed debug information is printed to stdout.
*   **Debugging Tools**:
    *   Run `python tools/list_models.py` to see available Gemini models in your project.
    *   Run `python tools/diagnose_model.py` to diagnose connection issues.
    *   If using High Fidelity mode, ensure your quota allows for the request size.
*   **Debugging Tools**:
    *   Run `python tools/list_models.py` to see available Gemini models in your project.
    *   Run `python tools/diagnose_model.py` to diagnose connection issues.

## Directory Structure

*   `app.py`: Main Gradio application.
*   `panorama_generator.py`: Core logic for interacting with Gemini API.
*   `prompts.py`: Storage for System Prompts.
*   `config.py`: Central configuration.
*   `outputs/`: Directory where generated images are saved.
*   `tools/`: Utility scripts for debugging and testing:
    *   `diagnose_model.py`: Diagnose Gemini model connection issues.
    *   `list_models.py`: List available Gemini models in your project.
*   `examples/`: Example scripts demonstrating advanced usage:
    *   `custom_prompt_example.py`: Example showing how to use custom prompts with command-line arguments.
