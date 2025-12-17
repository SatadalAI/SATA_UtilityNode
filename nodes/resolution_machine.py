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
        models = list(config["models"].keys())
        default_model = models[0] if models else "Unknown"

        # Collect ALL possible resolutions to pass validation
        all_resolutions = set(["Custom"])
        if "resolutions" in config:
            for bucket in config["resolutions"].values():
                for dim in bucket.values():
                    all_resolutions.update(dim.keys())
        
        # We can't sort mixed types effortlessly if any, but they are strings.
        # Sorting helps UI consistency if fallback happens, though JS overrides it.
        resolutions_list = sorted(list(all_resolutions))

        return {
            "required": {
                "model": (models, {"default": default_model}),
                "dimension": (["Square", "Portrait", "Landscape"],),
                "resolution": (resolutions_list,), 
                "custom_width": ("INT", {"default": 512, "min": 1, "max": 8192}),
                "custom_height": ("INT", {"default": 512, "min": 1, "max": 8192}),
            },
        }

    RETURN_TYPES = ("INT", "INT")
    RETURN_NAMES = ("width", "height")
    FUNCTION = "get_resolution"
    CATEGORY = "SATA_UtilityNode"

    def get_resolution(self, model, dimension, resolution, custom_width, custom_height):
        config = load_config()

        if model not in config["models"]:
            raise ValueError(f"[{NODE_NAME}] Unknown model: {model}")

        if resolution == "Custom":
            return (custom_width, custom_height)

        # Search for resolution string in the specific bucket/dimension
        # Iterate over tiers to find the bucket that has this model?
        # Actually config["models"][model] gives list of buckets.
        buckets = config["models"][model]
        
        resolution_data = None
        for bucket in buckets:
            # Check if this bucket has the selected dimension
            if bucket in config["resolutions"]:
                 if dimension in config["resolutions"][bucket]:
                     if resolution in config["resolutions"][bucket][dimension]:
                         resolution_data = config["resolutions"][bucket][dimension][resolution]
                         break
        
        if not resolution_data:
             # Fallback: maybe the user switched model and the resolution is now invalid, or it is custom manual
             # If "Custom" was passed, we handled it above.
             # If obscure mismatch, default to custom values provided
             print(f"[{NODE_NAME}] Warning: resolution '{resolution}' not found for model '{model}' dim '{dimension}', using Custom")
             return (custom_width, custom_height)

        return (resolution_data["width"], resolution_data["height"])


# --- REST endpoint for frontend config fetch ---
@PromptServer.instance.routes.get("/SATA_UtilityNode/resolutions_config")
async def get_resolutions_config(request):
    try:
        config = load_config()
        return web.json_response(config)
    except Exception as e:
        return web.json_response({"error": str(e)}, status=500)
