import json
import os
from server import PromptServer
from aiohttp import web

NODE_NAME = "Resolution_Machine"

# Path to JSON config (root of SATA_UtilityNode folder)
CONFIG_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "asset","resolutions.json"
)

def load_config():
    if not os.path.exists(CONFIG_PATH):
        raise FileNotFoundError(f"[{NODE_NAME}] resolutions.json not found at {CONFIG_PATH}")
    with open(CONFIG_PATH, "r", encoding="utf-8-sig") as f:
        return json.load(f)


class Resolution_Machine:
    @classmethod
    def INPUT_TYPES(cls):
        config = load_config()

        # all models
        # all models
        models = list(config["models"].keys())
        default_model = models[0] if models else "Unknown"

        # union of all resolutions across all tiers
        all_resolutions = set()
        for tier_res in config["resolutions"].values():
            all_resolutions.update(tier_res.keys())
        resolutions = sorted(list(all_resolutions))

        default_resolution = resolutions[0] if resolutions else "Custom (manual)"

        return {
            "required": {
                "model": (models, {"default": default_model}),
                "resolution": (resolutions, {"default": default_resolution}),
                "custom_width": ("INT", {"default": 512, "min": 1, "max": 8192}),
                "custom_height": ("INT", {"default": 512, "min": 1, "max": 8192}),
            },
            "optional": {
                "dimension_preview": ("STRING", {"multiline": False, "forceInput": False, "default": ""}),
            }
        }

    RETURN_TYPES = ("INT", "INT")
    RETURN_NAMES = ("width", "height")
    FUNCTION = "get_resolution"
    CATEGORY = "SATA_UtilityNode"

    def get_resolution(self, model, resolution, custom_width, custom_height, dimension_preview=None):
        config = load_config()

        if model not in config["models"]:
            raise ValueError(f"[{NODE_NAME}] Unknown model: {model}")

        # Search for resolution string in all tiers
        resolution_data = None
        for tier in config["resolutions"].values():
            if resolution in tier:
                resolution_data = tier[resolution]
                break

        if not resolution_data:
            # fallback to custom if not found
            print(f"[{NODE_NAME}] Warning: resolution '{resolution}' not found in definitions, defaulting to Custom")
            resolution = "Custom (manual)"
            resolution_data = {"width": 0, "height": 0}

        if resolution == "Custom (manual)":
            width, height = custom_width, custom_height
        else:
            width, height = resolution_data["width"], resolution_data["height"]


        return (width, height)


# --- REST endpoint for frontend config fetch ---
@PromptServer.instance.routes.get("/SATA_UtilityNode/resolutions_config")
async def get_resolutions_config(request):
    try:
        config = load_config()
        return web.json_response(config)
    except Exception as e:
        return web.json_response({"error": str(e)}, status=500)
