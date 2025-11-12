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

### 💾 Save Image w/Metadata

- **Single path+filename input:** Provide a single required `path_and_filename` string (examples: `comfy`, `Test/comfy`, `SDXL/Test/comfy`). The last path segment is used as the filename; preceding segments become folders under the ComfyUI output directory.
- **Supported formats:** PNG, JPEG (saved as .jpg), WEBP (choose with the `extension` dropdown).
- **Automatic folder creation:** Any missing folders in the provided path are created automatically.
- **Metadata embedding:** PNG files receive tEXt entries (parameters/prompt). JPEG/WEBP receive EXIF UserComment where possible.
- **Placeholder resolution:** Filenames and paths accept `%...%` placeholders which are resolved from the node's `prompt` dictionary (best-effort). Example: if `prompt` contains `{"title": "MyTitle"}`, using `%title%/img` will save under `MyTitle/img.png`.
- **Collision-safe saving:** If a file already exists the node will append `_0001`, `_0002`, ... to the base filename to avoid overwriting.


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

### 💾 Save Image w/Metadata — Inputs & Outputs

| Name               | Type    | Description |
|--------------------|---------|-------------|
| `path_and_filename`| STRING  | Single required path + filename string. Examples: `comfy`, `Test/comfy`, `SDXL/Test/comfy`. The last segment is used as filename (extension ignored); preceding segments are folder path under ComfyUI output directory. |
| `extension`        | STRING  | File format dropdown: `png`, `jpeg`, `webp`. |
| `custom_string`    | STRING  | Optional custom text to embed in metadata. |
| `quality_jpeg_or_webp` | INT | JPEG/WEBP quality (1-100). |
| `lossless_webp`    | BOOLEAN | If true, WEBP will be saved lossless (when supported). |

**Hidden inputs:**

- `prompt` — a dict-like object the node will consult to resolve `%...%` placeholders used in the `path_and_filename` string (best-effort lookup).

**Outputs:**

The node returns no tensor outputs but updates the UI with the list of saved filenames and their subfolders (so ComfyUI will display the saved files in the results panel).

**Behavior notes & examples:**

- If `path_and_filename` is `comfy` and `extension` is `png`, the node saves `OUTPUT_DIR/comfy.png` (or `comfy_0001.png` if it already exists).
- If `path_and_filename` is `SDXL/Test/comfy`, the node creates `OUTPUT_DIR/SDXL/Test/` if missing and saves `comfy.<ext>` inside it.
- You may use placeholders in `path_and_filename`, for example `%title%/img`, which will be resolved from the `prompt` dict when possible.


## 📝 License

MIT License

---

## 🔗 Links

- [ComfyUI](https://github.com/comfyanonymous/ComfyUI)