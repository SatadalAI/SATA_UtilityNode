import json
import os
from server import PromptServer
from aiohttp import web

NODE_NAME = "Resolution_Machine"

# Path to JSON config (root of SATA_UtilityNode folder)
CONFIG_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "resolutions.json"
)

def load_config():
    if not os.path.exists(CONFIG_PATH):
        raise FileNotFoundError(f"[{NODE_NAME}] resolutions.json not found at {CONFIG_PATH}")
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


class Resolution_Machine:
    @classmethod
    def INPUT_TYPES(cls):
        config = load_config()

        # all models
        models = list(config.keys())
        default_model = models[0] if models else "Unknown"

        # union of all resolutions across all models
        all_resolutions = set()
        for model_res in config.values():
            all_resolutions.update(model_res.keys())
        resolutions = sorted(list(all_resolutions))

        default_resolution = list(config[default_model].keys())[0]

        return {
            "required": {
                "model": (models, {"default": default_model}),
                "resolution": (resolutions, {"default": default_resolution}),
                "custom_width": ("INT", {"default": 512, "min": 1, "max": 8192}),
                "custom_height": ("INT", {"default": 512, "min": 1, "max": 8192}),
            }
        }

    RETURN_TYPES = ("INT", "INT")
    RETURN_NAMES = ("width", "height")
    FUNCTION = "get_resolution"
    CATEGORY = "SATA Utility"

    def get_resolution(self, model, resolution, custom_width, custom_height):
        config = load_config()

        if model not in config:
            raise ValueError(f"[{NODE_NAME}] Unknown model: {model}")

        resolutions = config[model]

        if resolution not in resolutions:
            # fallback to first available resolution for safety
            resolution = list(resolutions.keys())[0]
            print(f"[{NODE_NAME}] Warning: invalid resolution, defaulting to {resolution}")

        if resolution == "Custom (manual)":
            width, height = custom_width, custom_height
        else:
            entry = resolutions[resolution]
            width, height = entry["width"], entry["height"]

        print(f"[{NODE_NAME}] Model={model}, Resolution={resolution}, Output=({width}, {height})")
        return (width, height)


# --- REST endpoint for frontend config fetch ---
@PromptServer.instance.routes.get("/SATA_UtilityNode/resolutions_config")
async def get_resolutions_config(request):
    try:
        config = load_config()
        return web.json_response(config)
    except Exception as e:
        return web.json_response({"error": str(e)}, status=500)
