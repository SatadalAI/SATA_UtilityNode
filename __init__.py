from .nodes.combined_upscale import Combined_Upscale
from .nodes.prompt_machine import Prompt_Machine


NODE_CLASS_MAPPINGS = {
    "Combined_Upscale": Combined_Upscale,
    "Prompt_Machine": Prompt_Machine,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "Combined_Upscale": "Combined Upscale",
    "Prompt_Machine": "Prompt Machine",
}

WEB_DIRECTORY = "./web/js"

__all__ = ["WEB_DIRECTORY", "NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS"]