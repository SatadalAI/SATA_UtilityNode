import torch
import torch.nn.functional as F
import cv2
import numpy as np
import folder_paths
import comfy.utils
from comfy_extras.chainner_models import model_loading
from comfy import model_management


# Example ESRGAN-like model for demonstration.
# Replace this with your actual model class if different.
import torch.nn as nn

class YourModelClass(nn.Module):
    def __init__(self):
        super().__init__()
        # Minimal dummy model: identity (replace with your real model)
        # For a real upscaler, define layers here.
        # Example: self.conv = nn.Conv2d(3, 3, 3, padding=1)
    def forward(self, x):
        # Dummy: just return input (replace with real forward)
        return x

def load_model(model_name):
    model_path = folder_paths.get_full_path("upscale_models", model_name)
    sd = comfy.utils.load_torch_file(model_path, safe_load=True)
    # Remove "module." prefix if present (for DDP-trained models)
    if "module.layers.0.residual_group.blocks.0.norm1.weight" in sd:
        sd = comfy.utils.state_dict_prefix_replace(sd, {"module.":""})
    out = model_loading.load_state_dict(sd).eval()
    return out

def upscale_with_model(upscale_model, image):
    device = model_management.get_torch_device()
    upscale_model.to(device)
    in_img = image.movedim(-1, -3).to(device)
    tile = 512
    overlap = 32
    oom = True
    while oom:
        try:
            steps = in_img.shape[0] * comfy.utils.get_tiled_scale_steps(
                in_img.shape[3], in_img.shape[2], tile_x=tile, tile_y=tile, overlap=overlap
            )
            pbar = comfy.utils.ProgressBar(steps)
            s = comfy.utils.tiled_scale(
                in_img,
                lambda a: upscale_model(a),
                tile_x=tile,
                tile_y=tile,
                overlap=overlap,
                upscale_amount=upscale_model.scale,
                pbar=pbar
            )
            oom = False
        except model_management.OOM_EXCEPTION as e:
            tile //= 2
            if tile < 128:
                raise e
    upscale_model.cpu()
    s = torch.clamp(s.movedim(-3, -1), min=0, max=1.0)
    return [img for img in s]

def resize_tensor_opencv(tensor, target_width, target_height, supersample='true', factor=2.0):
    """
    CPU-based resizing using OpenCV for 'rescale' mode.
    """
    new_width = max(1, int(target_width))
    new_height = max(1, int(target_height))

    # Choose interpolation based on upscaling or downscaling
    interp = cv2.INTER_LANCZOS4 if factor > 1.0 else cv2.INTER_AREA

    np_img = tensor.mul(255).byte().cpu().numpy().transpose(1, 2, 0)
    if np_img.shape[0] == 0 or np_img.shape[1] == 0:
        raise ValueError("Input image for OpenCV resize has zero width or height.")

    if supersample == 'true':
        ss_width = max(1, new_width * 8)
        ss_height = max(1, new_height * 8)
        np_img = cv2.resize(np_img, (ss_width, ss_height), interpolation=interp)
        if np_img.shape[0] == 0 or np_img.shape[1] == 0:
            raise ValueError("Image became empty after supersample resize.")

    resized = cv2.resize(np_img, (new_width, new_height), interpolation=interp)
    return torch.from_numpy(resized.transpose(2, 0, 1)).float().div(255)

def resize_tensor_gpu(tensor, width, height, rounding_modulus):
    """
    GPU-based resizing using PyTorch interpolate for 'resize' mode.
    """
    new_width = width + (rounding_modulus - width % rounding_modulus) % rounding_modulus
    new_height = height + (rounding_modulus - height % rounding_modulus) % rounding_modulus

    tensor = tensor.unsqueeze(0).to(torch.float32)
    resized = F.interpolate(tensor, size=(new_height, new_width), mode="bicubic", align_corners=False)
    return resized.squeeze(0)

class Combined_Upscale:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "upscale_model": (folder_paths.get_filename_list("upscale_models"),),
                "mode": (["rescale", "resize"],),
                "rescale_factor": ("FLOAT", {"default": 2.0, "min": 0.01, "max": 16.0, "step": 0.01}),
                "resize_width": ("INT", {"default": 1024, "min": 1, "max": 48000, "step": 1}),
                "resize_height": ("INT", {"default": 1024, "min": 1, "max": 48000, "step": 1}),
                "supersample": (["true", "false"],),
                "rounding_modulus": ("INT", {"default": 8, "min": 8, "max": 1024, "step": 8}),
            }
        }

    RETURN_TYPES = ("IMAGE", "STRING",)
    RETURN_NAMES = ("IMAGE", "show_help",)
    FUNCTION = "upscale"
    CATEGORY = "SATA_UtilityNode"

    def upscale(self, image, upscale_model, rounding_modulus=8, mode="rescale", supersample='true',
                rescale_factor=2.0, resize_width=1024, resize_height=1024):

        up_model = load_model(upscale_model)
        up_image = upscale_with_model(up_model, image)

        original_width, original_height = image[0].shape[-1], image[0].shape[-2]
        show_help = "https://github.com/SatadalAI/help_image"

        scaled_images = []
        for img in up_image:
            if mode == "rescale":
                # Output size is always original * rescale_factor
                target_width = max(1, int(round(original_width * rescale_factor)))
                target_height = max(1, int(round(original_height * rescale_factor)))
                resized = resize_tensor_opencv(
                    img,
                    target_width,
                    target_height,
                    supersample,
                    rescale_factor
                )
            else:
                # Output size is always user-specified
                safe_width = max(1, int(resize_width))
                safe_height = max(1, int(resize_height))
                resized = resize_tensor_gpu(img, safe_width, safe_height, rounding_modulus)
            # Ensure output is 3-channel (RGB)
            if resized.dim() == 3 and resized.shape[0] == 1:
                resized = resized.repeat(3, 1, 1)
            elif resized.dim() == 3 and resized.shape[0] > 3:
                resized = resized[:3, :, :]
            elif resized.dim() == 2:
                resized = resized.unsqueeze(0).repeat(3, 1, 1)
            scaled_images.append(resized.unsqueeze(0))

        images_out = torch.cat(scaled_images, dim=0)
        return (images_out, show_help)