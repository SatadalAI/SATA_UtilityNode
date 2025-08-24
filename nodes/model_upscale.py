import comfy.utils
import comfy.model_management as mm
import folder_paths
from comfy_extras.chainner_models import model_loading
import torch

def load_model(model_name):
    path = folder_paths.get_full_path("upscale_models", model_name)
    sd = comfy.utils.load_torch_file(path, safe_load=True)
    if "module.layers.0.residual_group.blocks.0.norm1.weight" in sd:
        sd = comfy.utils.state_dict_prefix_replace(sd, {"module.": ""})
    return model_loading.load_state_dict(sd).eval()

def upscale_with_model(model, image):
    device = mm.get_torch_device()
    model.to(device)
    in_img = image.movedim(-1, -3).to(device)

    tile, overlap = 512, 32
    while True:
        try:
            steps = in_img.shape[0] * comfy.utils.get_tiled_scale_steps(
                in_img.shape[3], in_img.shape[2], tile_x=tile, tile_y=tile, overlap=overlap)
            pbar = comfy.utils.ProgressBar(steps)
            result = comfy.utils.tiled_scale(in_img, lambda a: model(a),
                                             tile_x=tile, tile_y=tile, overlap=overlap,
                                             upscale_amount=model.scale, pbar=pbar)
            break
        except mm.OOM_EXCEPTION:
            tile //= 2
            if tile < 128:
                raise

    model.cpu()
    return torch.clamp(result.movedim(-3, -1), min=0, max=1.0)