from .nodes.upscale_machine import Upscale_Machine
from .nodes.prompt_machine import Prompt_Machine
from .nodes.resolution_machine import Resolution_Machine
from .nodes.save_image_metadata import ImageSaveWithMetadata

NODE_CLASS_MAPPINGS = {
    "Upscale_Machine": Upscale_Machine,
    "Prompt_Machine": Prompt_Machine,
    "Resolution_Machine": Resolution_Machine,
    "Save_Image_Metadata": ImageSaveWithMetadata,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "Upscale_Machine": "Upscale Machine",
    "Prompt_Machine": "Prompt Machine",
    "Resolution_Machine": "Resolution Machine",
    "Save_Image_Metadata": "Save Image Metadata",
}

WEB_DIRECTORY = "./web"

__all__ = ["WEB_DIRECTORY", "NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS"]