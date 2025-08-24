# 🖼️ Combined Upscale Node for ComfyUI

**Author**: Satadal  
**Version**: 1.0  
**License**: MIT  
**Repository**: _[Add your GitHub link here]_  

## 🚀 Overview

`Combined_Upscale` is a custom ComfyUI node that intelligently upscales images using a selected model and then resizes them with fine-grained control. It combines model-based enhancement with flexible post-processing, making it ideal for workflows involving asset preparation, UI design, or high-quality image generation.

## ✨ Features

- 🔧 Model-based upscaling using custom or pre-trained models
- 📐 Resize modes: proportional rescale or fixed width
- 🧠 Supersampling for quality preservation
- 🎛️ Configurable resampling filters: `lanczos`, `bicubic`, `bilinear`, `nearest`
- 🧮 Rounding modulus for dimension alignment
- 📤 Returns both the processed image and a help link for reference

## 🧩 Node Inputs

| Name              | Type       | Description |
|-------------------|------------|-------------|
| `image`           | IMAGE      | Input image tensor |
| `upscale_model`   | STRING     | Filename of the model from `upscale_models` folder |
| `mode`            | STRING     | `"rescale"` or `"resize"` |
| `rescale_factor`  | FLOAT      | Scaling factor (used in `rescale` mode) |
| `resize_width`    | INT        | Target width (used in `resize` mode) |
| `resampling_method` | STRING   | Resampling filter |
| `supersample`     | STRING     | `"true"` or `"false"` |
| `rounding_modulus`| INT        | Ensures dimensions are divisible by this value |

## 📤 Node Outputs

| Name         | Type   | Description |
|--------------|--------|-------------|
| `IMAGE`      | IMAGE  | The upscaled and resized image |
| `show_help`  | STRING | Link to documentation or usage guide |

## 🛠️ Installation

1. Clone or download this repo into your ComfyUI `custom_nodes` directory:

```bash
git clone https://github.com/YOUR_USERNAME/Combined_Upscale.git