import torch
import cv2
import numpy as np
import folder_paths
import comfy.utils
from comfy import model_management
from spandrel import ModelLoader


def resize_tensor_opencv(tensor_chw, target_width, target_height, supersample='true', factor=2.0):
    """
    CPU-based resizing using OpenCV for 'rescale' mode.
    Input:  tensor_chw  -> torch.FloatTensor (C,H,W) in [0,1]
    Output: torch.FloatTensor (C,H,W) in [0,1], guaranteed 3-channel RGB
    """
    new_width = max(1, int(target_width))
    new_height = max(1, int(target_height))

    interp = cv2.INTER_LANCZOS4 if factor > 1.0 else cv2.INTER_AREA

    np_img = tensor_chw.permute(1, 2, 0).detach().cpu().numpy()
    np_img = (np.clip(np_img, 0.0, 1.0) * 255.0).astype(np.uint8)

    if np_img.ndim == 2: 
        np_img = cv2.cvtColor(np_img, cv2.COLOR_GRAY2RGB)
    elif np_img.shape[2] == 1:
        np_img = cv2.cvtColor(np_img, cv2.COLOR_GRAY2RGB)
    elif np_img.shape[2] == 4:
        np_img = cv2.cvtColor(np_img, cv2.COLOR_RGBA2RGB)
    elif np_img.shape[2] > 3: 
        np_img = np_img[:, :, :3]

    if np_img.shape[0] == 0 or np_img.shape[1] == 0:
        raise ValueError("Input image for OpenCV resize has zero width or height.")

    if supersample == 'true':
        ss_width = max(1, new_width * 8)
        ss_height = max(1, new_height * 8)
        np_img = cv2.resize(np_img, (ss_width, ss_height), interpolation=interp)
        if np_img.shape[0] == 0 or np_img.shape[1] == 0:
            raise ValueError("Image became empty after supersample resize.")

    resized = cv2.resize(np_img, (new_width, new_height), interpolation=interp)
    tensor_out = torch.from_numpy(resized).float().div(255.0).permute(2, 0, 1)
    return tensor_out


class Upscale_Machine:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "upscale_model": (folder_paths.get_filename_list("upscale_models"),),
                "rescale_factor": ("FLOAT", {"default": 2.0, "min": 0.01, "max": 16.0, "step": 0.01}),
                "supersample": (["true", "false"],),
                "rounding_modulus": ("INT", {"default": 8, "min": 1, "max": 1024, "step": 1}),
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

    def upscale_with_model(self, upscale_model, image_bhwc):
        """
        Run tiled upscale with spandrel model.
        Input:  image_bhwc -> (B,H,W,C) float [0,1]
        Output: (B,C,H',W') float [0,1]
        """
        device = model_management.get_torch_device()
        upscale_model.to(device)

        in_img = image_bhwc.movedim(-1, -3).to(device)

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
                    upscale_amount=getattr(upscale_model, "scale", 4),
                    pbar=pbar
                )
                oom = False
            except model_management.OOM_EXCEPTION as e:
                tile //= 2
                if tile < 128:
                    raise e

        upscale_model.cpu()
        s = torch.clamp(s, min=0.0, max=1.0) 
        return s

    def _round_to_modulus(self, value, modulus):
        if modulus is None or modulus <= 1:
            return int(max(1, round(value)))
        return max(modulus, int(round(value / modulus)) * modulus)

    def upscale(self, image, upscale_model, rounding_modulus=8, supersample='true',
                rescale_factor=2.0):


        if image.ndim != 4:
            raise ValueError("Expected IMAGE tensor with 4 dims (B,H,W,C).")

        original_height = int(image.shape[1])  
        original_width  = int(image.shape[2]) 


        target_width  = self._round_to_modulus(original_width  * rescale_factor, rounding_modulus)
        target_height = self._round_to_modulus(original_height * rescale_factor, rounding_modulus)


        up_model = self.load_model(upscale_model)
        up_bchw = self.upscale_with_model(up_model, image)

        batch_out = []
        for i in range(up_bchw.shape[0]):
            chw = up_bchw[i] 
            resized_chw = resize_tensor_opencv(
                chw, target_width=target_width, target_height=target_height,
                supersample=supersample, factor=rescale_factor
            )

            if resized_chw.shape[0] == 1:
                resized_chw = resized_chw.repeat(3, 1, 1)
            elif resized_chw.shape[0] > 3:
                resized_chw = resized_chw[:3, :, :]
            batch_out.append(resized_chw.unsqueeze(0)) 

        out_bchw = torch.cat(batch_out, dim=0) 

 
        images_out = out_bchw.movedim(1, -1).contiguous()

        show_help = "https://github.com/SatadalAI/help_image"
        return (images_out, show_help)