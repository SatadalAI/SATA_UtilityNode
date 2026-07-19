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
                "megapixel": (["None", "0.5MP", "1.0MP", "1.5MP", "2.0MP", "4.0MP"], {"default": "None"}),
            },
        }

    RETURN_TYPES = ("INT", "INT")
    RETURN_NAMES = ("width", "height")
    FUNCTION = "get_resolution"
    CATEGORY = "SATA_UtilityNode"

    def get_resolution(self, model, dimension, resolution, custom_width, custom_height, megapixel="None"):
        config = load_config()

        if model not in config["models"]:
            raise ValueError(f"[{NODE_NAME}] Unknown model: {model}")

        if resolution == "Custom":
            w, h = custom_width, custom_height
        else:
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
                 # If obscure mismatch, default to custom values provided
                 print(f"[{NODE_NAME}] Warning: resolution '{resolution}' not found for model '{model}' dim '{dimension}', using Custom")
                 w, h = custom_width, custom_height
            else:
                 w, h = resolution_data["width"], resolution_data["height"]

        if megapixel != "None":
            mp_map = {
                "0.5MP": 500000,
                "1.0MP": 1000000,
                "1.5MP": 1500000,
                "2.0MP": 2000000,
                "4.0MP": 4000000,
            }
            if megapixel in mp_map:
                P = mp_map[megapixel]
                R = float(w) / float(h)
                import math
                w_new = int(round(math.sqrt(P * R) / 8.0) * 8.0)
                h_new = int(round(math.sqrt(P / R) / 8.0) * 8.0)
                w = max(8, w_new)
                h = max(8, h_new)

        return (w, h)


# --- REST endpoint for frontend config fetch ---
@PromptServer.instance.routes.get("/SATA_UtilityNode/resolutions_config")
async def get_resolutions_config(request):
    try:
        config = load_config()
        return web.json_response(config)
    except Exception as e:
        return web.json_response({"error": str(e)}, status=500)
