# __init__.py

# Import all the node classes from the nodes directory
from .nodes.prompt_machine import Prompt_Machine
from .nodes.resolution_machine import Resolution_Machine
from .nodes.save_image_metadata import ImageSaveWithMetadata
from .nodes.upscale_machine import Upscale_Machine

# A dictionary that maps class names to class objects
NODE_CLASS_MAPPINGS = {
    "Prompt_Machine": Prompt_Machine,
    "Resolution_Machine": Resolution_Machine,
    "ImageSaveWithMetadata": ImageSaveWithMetadata,
    "Upscale_Machine": Upscale_Machine,
}

# A dictionary that maps display names to class names
NODE_DISPLAY_NAME_MAPPINGS = {
    "Prompt Machine": "Prompt_Machine",
    "Resolution Machine": "Resolution_Machine",
    "Save Image w/Metadata": "ImageSaveWithMetadata",
    "Upscale Machine": "Upscale_Machine",
}

# A dictionary that contains web directory information
WEB_DIRECTORY = "./js"

__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS', 'WEB_DIRECTORY']
