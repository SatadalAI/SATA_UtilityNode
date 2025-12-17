# __init__.py

# Import all the node classes from the nodes directory
from .nodes.prompt_machine import Prompt_Machine
from .nodes.resolution_machine import Resolution_Machine
from .nodes.save_machine import Save_Machine
from .nodes.upscale_machine import Upscale_Machine
from .nodes.prompt_autocomplete import PromptAutocomplete
from .nodes.latent_machine import Latent_Machine

# A dictionary that maps class names to class objects
NODE_CLASS_MAPPINGS = {
    "Prompt_Machine": Prompt_Machine,
    "Resolution_Machine": Resolution_Machine,
    "Save_Machine": Save_Machine,
    "Upscale_Machine": Upscale_Machine,
    "PromptAutocomplete": PromptAutocomplete,
    "Latent_Machine": Latent_Machine,
}

# A dictionary that maps display names to class names
NODE_DISPLAY_NAME_MAPPINGS = {
    "Prompt Machine": "Prompt_Machine",
    "Resolution Machine": "Resolution_Machine",
    "Save Machine": "Save_Machine",
    "Upscale Machine": "Upscale_Machine",
    "Prompt Autocomplete": "PromptAutocomplete",
    "Latent Machine": "Latent_Machine",
}

# A dictionary that contains web directory information
WEB_DIRECTORY = "./js"

__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS', 'WEB_DIRECTORY']
