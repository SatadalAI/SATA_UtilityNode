# SATA Utility Node Suite for ComfyUI

**Author:** Satadal  
**Version:** 1.5.0  
**License:** MIT  
**Repository:** https://github.com/SatadalAI/SATA_UtilityNode

---

## 🚀 Overview

SATA Utility Node Suite is a collection of custom nodes for [ComfyUI](https://github.com/comfyanonymous/ComfyUI) designed to enhance your image processing and workflow experience.  
It includes:

- **Upscale Machine:** High-quality model-based image upscaling with Frequency-Split SR and Blue Noise injection.
- **Prompt Machine (Six-Slot):** Professional structured prompting with JSON output support.
- **Prompt Style Machine:** Easy prompt selection from a CSV for positive/negative prompt workflows.
- **Touchpad Pan & Zoom:** Seamless navigation for large images in the ComfyUI preview panel.
- **Resolution Machine:** Quick selection of model-specific image resolutions with intelligent Megapixel scaling.
- **Save Image w/Metadata:** Saving images with metadata and with different file formats.
- **Prompt Autocomplete:** Text widget with highly optimized subsequence fuzzy autocompletion.
- **Latent Machine:** Advanced noise generation (Power-Law, Plasma, Blue, Offset) supporting both 4-channel and 16-channel modern architectures.
- **Preview Machine:** Privacy-focused image preview node with auto-hide and hover-to-reveal functionality.

---

## 🧩 Node Features

### 🖼️ Upscale Machine

- **Model-based Upscaling:** Uses custom or pre-trained models from the `upscale_models` folder.
- **Frequency-Split SR:** Separates image into base colors (low frequencies) and sharp edges (high frequencies). The neural network only upscales edges, while a bicubic algorithm scales colors, eliminating "plastic/waxy" looks and edge halos.
- **Blue Noise Injection:** Adds high-frequency micro-textures (`inject_noise_for_realism`) during upscaling. Automatically activates when using a chained model to fix the "smoothness" problem in low-step/distilled models like SDXL Turbo.
- **Aspect Ratio Preserving Rescale:** Output size is always original size × rescale factor.
- **CPU-based Rescaling:** Efficient resizing using OpenCV.
- **Rounding Modulus:** Ensures output dimensions seamlessly align with UNet architectural constraints.

### 💬 Prompt Machine (Six-Slot Framework)

- **Structured Prompting:** Dedicated input boxes for `subject`, `style`, `lighting`, `composition`, `mood`, and `technical` details to prevent "word salad".
- **JSON Output Mode:** Toggle `json_output` to compile the slots into a strict JSON string, perfect for piping into LLM rewriting nodes or API pipelines.
- **Autocomplete Ready:** Fully integrated with the autocomplete system—just type `#` in any slot to trigger the smart tag popup!
- **Natural Language & Comma Separated:** Dynamically formats outputs for FLUX (Natural Language) or SDXL (Comma Separated).

### 💬 Prompt Style Machine (Legacy)

- **CSV-based Prompt Selection:** Select prompt sets from a CSV file (`prompts.csv`).
- **Clean Output:** Outputs the positive prompt string with a live, enlarged text preview inside the node.

### 🖱️ Touchpad Pan & Zoom

- **Preview Navigation:** Enables smooth pan and zoom for large images in the ComfyUI preview panel.
- **User Experience:** Makes inspecting high-res outputs fast and intuitive.

### 📏 Resolution Machine

- **Intelligent Megapixel Scaling:** Uses a target Megapixel slider to automatically calculate the exact width/height required to hit the target while perfectly preserving your chosen aspect ratio. Rounds to the nearest multiple of 8.
- **Model-aware Resolution Selection:** Choose from a list of recommended resolutions for each supported model (SD1.5, SDXL, Flux.1 & Flux.2, SD3 & SD3.5, Ideogram 4, Lumina, Qwen-Image, Z-Image Turbo, Hunyuan-DiT, and Video Models like Wan2.2, HunyuanVideo, Mochi-1, LTX-Video).

---

### 💾 Save Image w/Metadata

- **Single path+filename input:** Provide a single required `path_and_filename` string.
- **Supported formats:** PNG, JPEG (saved as .jpg), WEBP (choose with the `extension` dropdown).
- **Automatic folder creation:** Any missing folders in the provided path are created automatically.
- **Metadata embedding:** PNG files receive tEXt entries (parameters/prompt). JPEG/WEBP receive EXIF UserComment where possible.
- **Placeholder resolution:** Filenames and paths accept `%...%` placeholders which are resolved from the node's `prompt` dictionary.
- **Collision-safe saving:** Automatically appends numerical suffixes to avoid overwriting.

### ✍️ Prompt Autocomplete

- **Subsequence Fuzzy Matching:** Ultra-fast, highly optimized fuzzy search with rank-based scoring.
- **Autocompletion:** Type `#` (configurable) to trigger a popup with suggestions from CSV/JSON files in the `prompt` folder. Supports strict 100-item render limits to prevent UI lag.
- **Random Selection:** Select `🎲 Random` to insert a random item from a category.
- **Global Mode:** Optional setting to enable autocompletion on ALL text widgets in ComfyUI.

### 🌌 Latent Machine

- **Advanced Noise Generation:** Initialize latents with specific noise patterns:
    - **Gaussian (White):** Standard noise, good for sharp details.
    - **Blue (High-Frequency):** Enhances detail and textures.
    - **Pink (1/f) / Brown (1/f²):** Photorealism, nature, anime backgrounds.
    - **Perlin / Plasma:** Fluid landscapes, sci-fi, abstract terrains.
- **High-Contrast Offset Noise:** Toggle `high_contrast` to inject a `0.1` mean shift to the starting noise, allowing the model to generate pure blacks (pitch-black nights) and blown-out whites (snowstorms).
- **Auto 16-Channel Detection:** Automatically provisions the correct latent depth for modern architectures (Flux, SD3, Lumina, Z-Image).
- **Reproducibility:** Full seed support for consistent noise generation.

### 👁️ Preview Machine

- **Privacy-Focused Preview:** Image preview node that hides content by default.
- **Hover to Reveal / Auto-Hide:** Simply hover over the node to temporarily reveal the image.
- **Global Hide Mode:** Optional setting to hide ALL preview nodes in the workflow (Settings → SATA Utility: Global Hide Previews).

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

**Settings:**
- **Trigger Character:** Change the character that opens the popup (default: `#`).
- **Global Mode:** Enable autocompletion for all text widgets in ComfyUI (default: `false`).

## 📝 License

MIT License

---

## 🔗 Links

- [ComfyUI](https://github.com/comfyanonymous/ComfyUI)