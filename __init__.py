from .nodes.combined_upscale import Combined_Upscale

NODE_CLASS_MAPPINGS = {
    "Combined_Upscale": Combined_Upscale,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "Combined_Upscale": "Combined_Upscale",
}

WEB_DIRECTORY = "./web/js"

__all__ = ["WEB_DIRECTORY", "NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS"]