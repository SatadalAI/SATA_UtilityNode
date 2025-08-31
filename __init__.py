from .nodes.upscale_machine import Upscale_Machine
from .nodes.prompt_machine import Prompt_Machine


NODE_CLASS_MAPPINGS = {
    "Upscale_Machine": Upscale_Machine,
    "Prompt_Machine": Prompt_Machine,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "Upscale_Machine": "Upscale Machine",
    "Prompt_Machine": "Prompt Machine",
}

WEB_DIRECTORY = "./web"

__all__ = ["WEB_DIRECTORY", "NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS"]