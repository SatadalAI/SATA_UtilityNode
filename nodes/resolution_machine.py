from server import PromptServer
from aiohttp import web

class Resolution_Machine:
    CATEGORY = "SATA_UtilityNode"

    # persist last-used selections
    last_model = None
    last_resolution = None
    last_width = None
    last_height = None

    @classmethod
    def _get_config(cls):
        cfg = {
          "models": [
            {
              "model": "SD1.5",
              "resolutions": [
                { "name": "Square (1:1)", "width": 512, "height": 512 },
                { "name": "Square high-res (1:1)", "width": 768, "height": 768 },
                { "name": "Landscape (3:2)", "width": 768, "height": 512 },
                { "name": "Portrait (2:3)", "width": 512, "height": 768 },
                { "name": "Landscape (4:3)", "width": 768, "height": 576 },
                { "name": "Portrait (3:4)", "width": 576, "height": 768 },
                { "name": "Widescreen (16:9)", "width": 912, "height": 512 },
                { "name": "Tall (9:16)", "width": 512, "height": 912 }
              ]
            },
            {
              "model": "SDXL",
              "resolutions": [
                { "name": "Square (1:1 native)", "width": 1024, "height": 1024 },
                { "name": "Portrait (2:3)", "width": 832, "height": 1216 },
                { "name": "Standard (3:4)", "width": 880, "height": 1176 },
                { "name": "Large Format (4:5)", "width": 912, "height": 1144 },
                { "name": "SD TV (4:3)", "width": 1176, "height": 888 },
                { "name": "IMAX (1.43:1)", "width": 1224, "height": 856 },
                { "name": "Golden Ratio (1.618:1)", "width": 1296, "height": 800 },
                { "name": "European Widescreen (1.66:1)", "width": 1312, "height": 792 },
                { "name": "Widescreen / HD TV (16:9)", "width": 1360, "height": 768 },
                { "name": "Standard Widescreen (1.85:1)", "width": 1392, "height": 752 },
                { "name": "Cinemascope / Panavision (2.35:1)", "width": 1568, "height": 664 },
                { "name": "Anamorphic Widescreen (2.39:1)", "width": 1576, "height": 656 },
                { "name": "Older TV & Documentaries (4:3)", "width": 1176, "height": 880 }
              ]
            },
            {
              "model": "Illustrious XL",
              "resolutions": [
                { "name": "Minimum training bound", "width": 512, "height": 512 },
                { "name": "standard example", "width": 1024, "height": 1024 },
                { "name": "Standard high-res", "width": 1536, "height": 1536 },
                { "name": "Maximum native", "width": 2048, "height": 2048 },
                { "name": "Portrait-tall", "width": 832, "height": 1216 },
                { "name": "Landscape-wide", "width": 1216, "height": 832 },
                { "name": "Square (1:1)", "width": 1024, "height": 1024 }
              ]
            },
            {
              "model": "Flux.1 Dev",
              "resolutions": [
                { "name": "512×512 (1 MP quick test)", "width": 512, "height": 512 },
                { "name": "1024×1024 (daily work)", "width": 1024, "height": 1024 },
                { "name": "1600×1600 (detailed work)", "width": 1600, "height": 1600 },
                { "name": "1920×1080 (HD)", "width": 1920, "height": 1080 },
                { "name": "2560×1440 (QHD)", "width": 2560, "height": 1440 },
                { "name": "3840×2160 (4K)", "width": 3840, "height": 2160 }
              ]
            },
            {
              "model": "Qwen-Image",
              "resolutions": [
                { "name": "Square (1:1)", "width": 1328, "height": 1328 },
                { "name": "Widescreen (16:9)", "width": 1664, "height": 928 },
                { "name": "Tall (9:16)", "width": 928, "height": 1664 },
                { "name": "Landscape (4:3)", "width": 1472, "height": 1140 },
                { "name": "Portrait (3:4)", "width": 1140, "height": 1472 }
              ]
            },
            {
              "model": "Wan2.2-S2V",
              "resolutions": [
                { "name": "720p HD video", "width": 1280, "height": 720 }
              ]
            },
            {
              "model": "SD3.5 Large",
              "resolutions": [
                { "name": "768×1152 (best portrait)", "width": 768, "height": 1152 },
                { "name": "1152×768 (best landscape)", "width": 1152, "height": 768 },
                { "name": "1024×1024 (square)", "width": 1024, "height": 1024 },
                { "name": "768×768 (quick test)", "width": 768, "height": 768 },
                { "name": "832×1216 portrait", "width": 832, "height": 1216 },
                { "name": "1216×832 landscape", "width": 1216, "height": 832 }
              ]
            }
          ]
        }

        # Append Custom option idempotently
        for m in cfg["models"]:
            if not any(r["name"] == "Custom (manual)" for r in m.get("resolutions", [])):
                m.setdefault("resolutions", []).append({"name": "Custom (manual)", "width": 0, "height": 0})

        return cfg

    @classmethod
    def INPUT_TYPES(cls, context=None):
        cfg = cls._get_config()
        models = [m["model"] for m in cfg["models"]]

        # restore last used model or default
        default_model = cls.last_model if cls.last_model in models else (models[0] if models else "")

        model_obj = next((m for m in cfg["models"] if m["model"] == default_model), None)
        if model_obj:
            resolutions = [r["name"] for r in model_obj.get("resolutions", [])]
        else:
            resolutions = ["Custom (manual)"]

        # restore last used resolution if valid
        if cls.last_resolution and cls.last_resolution in resolutions:
            default_res = cls.last_resolution
        else:
            default_res = next((n for n in resolutions if n != "Custom (manual)"), resolutions[0])

        # determine defaults for width/height
        default_w, default_h = 512, 512
        if cls.last_width and cls.last_height:
            default_w, default_h = cls.last_width, cls.last_height
        else:
            r_obj = next((r for r in model_obj["resolutions"] if r["name"] == default_res), None) if model_obj else None
            if r_obj:
                default_w, default_h = r_obj["width"], r_obj["height"]

        return {
            "required": {
                "model": (models if models else ["null"], {"default": default_model}),
                "resolution": (resolutions if resolutions else ["Custom (manual)"], {"default": default_res}),
                "width": ("INT", {"default": default_w, "min": 1, "max": 16384, "step": 1}),
                "height": ("INT", {"default": default_h, "min": 1, "max": 16384, "step": 1}),
            }
        }

    RETURN_TYPES = ("INT", "INT")
    RETURN_NAMES = ("width", "height")
    FUNCTION = "run"

    def run(self, model, resolution, width, height):
        cfg = self._get_config()
        model_obj = next((m for m in cfg["models"] if m["model"] == model), None)
        if model_obj and resolution and resolution != "Custom (manual)":
            res_obj = next((r for r in model_obj["resolutions"] if r["name"] == resolution), None)
            if res_obj:
                width, height = res_obj["width"], res_obj["height"]

        # store last selections for persistence
        Resolution_Machine.last_model = model
        Resolution_Machine.last_resolution = resolution
        Resolution_Machine.last_width = width
        Resolution_Machine.last_height = height

        return width, height


# REST endpoint for frontend dynamic updates
@PromptServer.instance.routes.get("/sata/resolution_machine/config")
async def get_resolution_config(request):
    return web.json_response(Resolution_Machine._get_config())