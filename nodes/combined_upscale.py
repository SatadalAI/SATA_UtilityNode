import torch
import torch.nn.functional as F
import cv2
import numpy as np
import folder_paths
import comfy.utils
from comfy import model_management
from spandrel import ModelLoader


def resize_tensor_opencv(tensor, target_width, target_height, supersample='true', factor=2.0):
    """
    CPU-based resizing using OpenCV for 'rescale' mode.
    Ensures output is always 3-channel RGB.
    """
    new_width = max(1, int(target_width))
    new_height = max(1, int(target_height))

    # Choose interpolation based on upscaling or downscaling
    interp = cv2.INTER_LANCZOS4 if factor > 1.0 else cv2.INTER_AREA

    # Convert (C,H,W) torch → (H,W,C) numpy
    np_img = tensor.mul(255).byte().cpu().numpy().transpose(1, 2, 0).copy()

    if np_img.shape[0] == 0 or np_img.shape[1] == 0:
        raise ValueError("Input image for OpenCV resize has zero width or height.")

    # Force 3-channel RGB (expand grayscale or truncate >3)
    if np_img.ndim == 2:  # pure grayscale
        np_img = cv2.cvtColor(np_img, cv2.COLOR_GRAY2RGB)
    elif np_img.shape[2] == 1:  # single channel
        np_img = cv2.cvtColor(np_img, cv2.COLOR_GRAY2RGB)
    elif np_img.shape[2] > 3:  # drop extra channels (e.g. alpha)
        np_img = np_img[:, :, :3]

    if supersample == 'true':
        ss_width = max(1, new_width * 8)
        ss_height = max(1, new_height * 8)
        np_img = cv2.resize(np_img, (ss_width, ss_height), interpolation=interp)
        if np_img.shape[0] == 0 or np_img.shape[1] == 0:
            raise ValueError("Image became empty after supersample resize.")

    resized = cv2.resize(np_img, (new_width, new_height), interpolation=interp)

    # Back to (C,H,W) torch float
    return torch.from_numpy(resized.transpose(2, 0, 1)).float().div(255)


class Combined_Upscale:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "upscale_model": (folder_paths.get_filename_list("upscale_models"),),
                "rescale_factor": ("FLOAT", {"default": 2.0, "min": 0.01, "max": 16.0, "step": 0.01}),
                "supersample": (["true", "false"],),
                "rounding_modulus": ("INT", {"default": 8, "min": 8, "max": 1024, "step": 8}),
            }
        }

    RETURN_TYPES = ("IMAGE", "STRING",)
    RETURN_NAMES = ("IMAGE", "show_help",)
    FUNCTION = "upscale"
    CATEGORY = "SATA_UtilityNode"

    def load_model(self, model_name):
        """Load ESRGAN/RealESRGAN/AESRGAN via spandrel"""
        model_path = folder_paths.get_full_path("upscale_models", model_name)
        model_loader = ModelLoader()
        model = model_loader.load_from_file(model_path)

        if model is None:
            raise RuntimeError(f"Failed to load upscale model: {model_name}")

        model.eval()
        return model

    def upscale_with_model(self, upscale_model, image):
        """Run tiled upscale with spandrel model"""
        device = model_management.get_torch_device()
        upscale_model.to(device)

        in_img = image.movedim(-1, -3).to(device)  # (B,H,W,C) → (B,C,H,W)

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
                    upscale_amount=getattr(upscale_model, "scale", 4),  # fallback=4
                    pbar=pbar
                )
                oom = False
            except model_management.OOM_EXCEPTION as e:
                tile //= 2
                if tile < 128:
                    raise e

        upscale_model.cpu()
        s = torch.clamp(s.movedim(-3, -1), min=0, max=1.0)  # (B,H,W,C)
        return [img for img in s]

    def upscale(self, image, upscale_model, rounding_modulus=8, supersample='true',
                rescale_factor=2.0):

        up_model = self.load_model(upscale_model)
        up_image = self.upscale_with_model(up_model, image)

        original_width, original_height = image[0].shape[-1], image[0].shape[-2]
        show_help = "https://github.com/SatadalAI/help_image"

        scaled_images = []
        for img in up_image:
            target_width = max(1, int(round(original_width * rescale_factor)))
            target_height = max(1, int(round(original_height * rescale_factor)))
            resized = resize_tensor_opencv(img, target_width, target_height, supersample, rescale_factor)
            scaled_images.append(resized.unsqueeze(0))

        images_out = torch.cat(scaled_images, dim=0)
        return (images_out, show_help)