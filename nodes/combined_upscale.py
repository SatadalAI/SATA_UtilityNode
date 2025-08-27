from .model_upscale import load_model, upscale_with_model
from .resize_utils import resize_tensor_opencv, resize_tensor_gpu
import folder_paths
import torch

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

        if up_image[0].shape[-1] == original_width and rescale_factor == 1:
            return (up_image, show_help)

        scaled_images = []
        for img in up_image:
            if mode == "rescale":
                # Calculate new dimensions, ensure they are at least 1
                new_width = max(1, int(original_width * rescale_factor))
                new_height = max(1, int(original_height * rescale_factor))
                # Pass safe values to resize_tensor_opencv
                resized = resize_tensor_opencv(
                    img,
                    new_width,
                    new_height,
                    rounding_modulus,
                    mode,
                    supersample,
                    rescale_factor,
                    resize_width
                )
            else:
                # Ensure resize_width and resize_height are at least 1
                safe_width = max(1, int(resize_width))
                safe_height = max(1, int(resize_height))
                resized = resize_tensor_gpu(img, safe_width, safe_height, rounding_modulus)
            scaled_images.append(resized.unsqueeze(0))

        images_out = torch.cat(scaled_images, dim=0)
        return (images_out, show_help)