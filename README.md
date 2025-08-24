# 🖼️ Combined Upscale Node for ComfyUI

**Author**: Satadal  
**Version**: 1.0  
**License**: MIT  
**Repository**: https://github.com/SatadalAI/SATA_UtilityNode 

---

## 🚀 Overview

`Combined_Upscale` is a custom ComfyUI node designed for high-quality image enhancement workflows. It intelligently combines model-based upscaling with efficient CPU-based resizing, offering granular control over output dimensions and quality. Ideal for asset pipelines, UI prototyping, and generative workflows.

---

## ✨ Features

- 🔧 **Model-based Upscaling**  
  Uses custom or pre-trained models from the `upscale_models` folder for deep enhancement.

- 📐 **CPU-based Rescaling**  
  Efficient resizing using OpenCV interpolation—no GPU required for post-processing.

- 🧠 **Supersampling Support**  
  Optional supersampling to preserve detail during downscaling or fractional resizing.

- 🎛️ **Flexible Resampling Filters**  
  Choose from `lanczos`, `bicubic`, `bilinear`, or `nearest` for tailored output.

- 🧮 **Rounding Modulus**  
  Ensures output dimensions align with model or UI constraints (e.g. divisible by 8 or 64).

- 🖱️ **Touchpad Pan & Zoom Support**  
  Seamless navigation in the ComfyUI preview panel when inspecting large outputs.

- 📤 **Dual Output**  
  Returns both the processed image and a help link for quick reference or documentation.

---

## 🧩 Node Inputs

| Name                | Type    | Description |
|---------------------|---------|-------------|
| `image`             | IMAGE   | Input image tensor |
| `upscale_model`     | STRING  | Filename of the model from `upscale_models` folder |
| `mode`              | STRING  | `"rescale"` or `"resize"` |
| `rescale_factor`    | FLOAT   | Scaling factor (used in `rescale` mode) |
| `resize_width`      | INT     | Target width (used in `resize` mode) |
| `resampling_method` | STRING  | Resampling filter |
| `supersample`       | STRING  | `"true"` or `"false"` |
| `rounding_modulus`  | INT     | Ensures dimensions are divisible by this value |

---

## 📤 Node Outputs

| Name         | Type   | Description |
|--------------|--------|-------------|
| `IMAGE`      | IMAGE  | The upscaled and resized image |
| `show_help`  | STRING | Link to documentation or usage guide |

---

## 🛠️ Installation

Clone or download this repo into your ComfyUI `custom_nodes` directory:

git clone https://github.com/SatadalAI/SATA_UtilityNode.git