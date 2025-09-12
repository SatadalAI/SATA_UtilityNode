# SATA Utility Node Suite for ComfyUI

**Author:** Satadal  
**Version:** 1.0  
**License:** MIT  
**Repository:** https://github.com/SatadalAI/SATA_UtilityNode

---

## 🚀 Overview

SATA Utility Node Suite is a collection of custom nodes for [ComfyUI](https://github.com/comfyanonymous/ComfyUI) designed to enhance your image processing and workflow experience.  
It includes:

- **Upscale Machine:** High-quality model-based image upscaling with aspect-ratio preserving rescale.
- **Prompt Machine:** Easy prompt selection from a CSV for positive/negative prompt workflows.
- **Touchpad Pan & Zoom:** Seamless navigation for large images in the ComfyUI preview panel.
- **Resolution Machine:** Quick selection of model-specific image resolutions for popular models.

---

## 🧩 Node Features

### 🖼️ Upscale Machine

- **Model-based Upscaling:** Uses custom or pre-trained models from the `upscale_models` folder.
- **Aspect Ratio Preserving Rescale:** Output size is always original size × rescale factor.
- **CPU-based Rescaling:** Efficient resizing using OpenCV.
- **Supersampling:** Optional detail preservation for downscaling/fractional resizing.
- **Rounding Modulus:** Ensures output dimensions align with model/UI constraints.
- **Dual Output:** Returns both the processed image and a help/documentation link.

### 💬 Prompt Machine

- **CSV-based Prompt Selection:** Select prompt sets from a CSV file (`prompts.csv`).
- **Positive/Negative Output:** Outputs both positive and negative prompts as strings.
- **Easy Integration:** Designed for use in prompt-driven workflows.

### 🖱️ Touchpad Pan & Zoom

- **Preview Navigation:** Enables smooth pan and zoom for large images in the ComfyUI preview panel.
- **User Experience:** Makes inspecting high-res outputs fast and intuitive.

### 📏 Resolution Machine

- **Model-aware Resolution Selection:** Choose from a list of recommended resolutions for each supported model.
- **Auto-populate Width/Height:** Selecting a resolution automatically fills in the correct width and height.
- **Manual Override:** You can manually set width/height, which clears the preset selection.
- **Supports Many Models:** Includes presets for SD1.5, SDXL, Illustrious XL, Pony XL, Flux.1 Dev, Qwen-Image, Wan2.2-S2V, SD3.5 Large, Lumina-Image 2.0, and more.
- **UI Integration:** Intuitive dropdowns for model and resolution selection in the ComfyUI interface.

---

## 📦 Installation

1. Clone or download this repository into your ComfyUI `custom_nodes` directory:

   ```sh
   git clone https://github.com/SatadalAI/SATA_UtilityNode.git
   ```

2. (Optional) Install dependencies if not already present:

   ```sh
   pip install -r requirements.txt
   ```

3. Restart ComfyUI.

---

## 📚 Node Inputs & Outputs

### Upscale Machine

| Name             | Type   | Description                                      |
|------------------|--------|--------------------------------------------------|
| `image`          | IMAGE  | Input image tensor                               |
| `upscale_model`  | STRING | Model filename from `upscale_models` folder      |
| `rescale_factor` | FLOAT  | Scaling factor (aspect ratio preserved)          |
| `supersample`    | STRING | `"true"` or `"false"`                            |
| `rounding_modulus` | INT  | Ensures dimensions are divisible by this value   |

**Outputs:**

| Name        | Type   | Description                        |
|-------------|--------|------------------------------------|
| `IMAGE`     | IMAGE  | The upscaled and resized image     |
| `show_help` | STRING | Link to documentation/help         |

---

### Prompt Machine

| Name        | Type   | Description                        |
|-------------|--------|------------------------------------|
| `selection` | STRING | Prompt set name from CSV           |

**Outputs:**

| Name        | Type   | Description                        |
|-------------|--------|------------------------------------|
| `positive`  | STRING | Positive prompt                    |
| `negative`  | STRING | Negative prompt                    |

---

### Touchpad Pan & Zoom

- **No node configuration required.**  
- Enables pan/zoom in the ComfyUI preview panel for large images.

---

### Resolution Machine

| Name         | Type   | Description                                      |
|--------------|--------|--------------------------------------------------|
| `model`      | STRING | Model name (select from supported models)        |
| `resolution` | STRING | Resolution preset name (auto-populates size)     |
| `width`      | INT    | Image width (can be set manually)                |
| `height`     | INT    | Image height (can be set manually)               |

**Outputs:**

| Name     | Type | Description                |
|----------|------|----------------------------|
| `width`  | INT  | Final image width          |
| `height` | INT  | Final image height         |

---

## 📝 License

MIT License

---

## 🔗 Links

- [ComfyUI](https://github.com/comfyanonymous/ComfyUI)
- [SATA Utility Node GitHub](https://github.com/SatadalAI/SATA_UtilityNode)