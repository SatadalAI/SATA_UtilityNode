import cv2
import torch
import numpy as np
import torch.nn.functional as F

def resize_tensor_opencv(tensor, original_width, original_height, rounding_modulus,
                         mode='rescale', supersample='true', factor=2, width=1024, height=None):
    """
    CPU-based resizing using OpenCV for 'rescale' mode.
    """
    if mode == 'rescale':
        new_width = int(original_width * factor)
        new_height = int(original_height * factor)
    else:
        raise ValueError("resize_tensor_opencv should only be used for 'rescale' mode.")

    interp = cv2.INTER_LANCZOS4 if factor > 1.0 else cv2.INTER_AREA

    np_img = tensor.mul(255).byte().cpu().numpy().transpose(1, 2, 0)

    if supersample == 'true':
        np_img = cv2.resize(np_img, (new_width * 8, new_height * 8), interpolation=interp)

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