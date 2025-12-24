from nodes import PreviewImage 

class Preview_Machine(PreviewImage):
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "images": ("IMAGE",),
            },
            "hidden": {"prompt": "PROMPT", "extra_pnginfo": "EXTRA_PNGINFO"},
        }

    RETURN_TYPES = ()
    OUTPUT_NODE = True
    CATEGORY = "SATA_UtilityNode"
    FUNCTION = "save_images"

    def save_images(self, images, prompt=None, extra_pnginfo=None):
        return super().save_images(images, filename_prefix="Preview_Machine", prompt=prompt, extra_pnginfo=extra_pnginfo)
