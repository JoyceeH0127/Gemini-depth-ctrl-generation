# Examples

This directory contains example scripts demonstrating how to use the PanoramaGenerator in different scenarios.

## Available Examples

### `custom_prompt_example.py`

Demonstrates how to use custom prompts to modify the generated panorama. This example shows how to:
- Load RGB and Depth images from command line arguments
- Use custom prompts (from command line, file, or built-in examples)
- Generate panoramas with specific modifications
- Save the results

#### Usage

```bash
# Basic usage with built-in example prompt (red car modification)
python examples/custom_prompt_example.py \
    --rgb path/to/rgb_image.png \
    --depth path/to/depth_image.png

# Use custom prompt from command line
python examples/custom_prompt_example.py \
    --rgb rgb.png \
    --depth depth.png \
    --prompt "Change the sky to a sunset scene"

# Use custom prompt from file
python examples/custom_prompt_example.py \
    --rgb rgb.png \
    --depth depth.png \
    --prompt-file my_custom_prompt.txt

# Specify output path and temperature
python examples/custom_prompt_example.py \
    --rgb rgb.png \
    --depth depth.png \
    --output outputs/my_result.png \
    --temperature 0.3
```

#### Options

- `--rgb`: Path to RGB reference image (required)
- `--depth`: Path to Depth map image (required)
- `--output`: Output path (default: `outputs/custom_panorama.png`)
- `--prompt`: Custom prompt text
- `--prompt-file`: Path to file containing custom prompt
- `--example-prompt`: Use built-in example prompt (red car modification)
- `--temperature`: Temperature for generation (default: 0.4)

## Creating Your Own Examples

When creating new example scripts:

1. Place them in this `examples/` directory
2. Add proper command-line argument parsing
3. Include docstrings and usage examples
4. Update this README with a description
