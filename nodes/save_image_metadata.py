import os
import hashlib
from datetime import datetime
import json
import piexif
import piexif.helper
from PIL import Image
from PIL.PngImagePlugin import PngInfo
import numpy as np
import folder_paths
import re


def parse_name(ckpt_name):
    path = ckpt_name
    filename = path.split("/")[-1]
    filename = filename.split(".")[:-1]
    filename = ".".join(filename)
    return filename


def calculate_sha256(file_path):
    sha256_hash = hashlib.sha256()

    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)

    return sha256_hash.hexdigest()


def handle_whitespace(string: str):
    return string.strip().replace("\n", " ").replace("\r", " ").replace("\t", " ")


def get_timestamp(time_format):
    now = datetime.now()
    try:
        timestamp = now.strftime(time_format)
    except:
        timestamp = now.strftime("%Y-%m-%d-%H%M%S")

    return timestamp


def make_pathname(template: str):
    """Simple pathname templating: supports %date and %time."""
    template = template.replace("%date", get_timestamp("%Y-%m-%d"))
    template = template.replace("%time", get_timestamp("%Y-%m-%d-%H%M%S"))
    return template


def make_filename(template: str):
    """Return a resolved filename from template; if empty, return a timestamp."""
    filename = make_pathname(template)
    return get_timestamp("%Y-%m-%d-%H%M%S") if filename == "" else filename


def resolve_placeholders(template: str, prompt=None) -> str:
    """Resolve placeholders of the form %node_name/field% by looking into extra_pnginfo and prompt.

    This is a best-effort resolver: it attempts several lookup strategies and falls back to leaving
    the placeholder unchanged when a value can't be found.
    """
    if not template or '%' not in template:
        return template

    def lookup(key: str):
        # key is like 'node_name/field' or 'field'
        if not key:
            return None
        # Try prompt mapping
        if prompt and isinstance(prompt, dict):
            if key in prompt:
                return prompt[key]
            if '/' in key:
                _, field = key.split('/', 1)
                if field in prompt:
                    return prompt[field]

        return None

    pattern = re.compile(r"%([^%]+)%")

    def repl(m):
        key = m.group(1)
        val = lookup(key)
        if val is None:
            return m.group(0)
        # If value is a list/dict, JSON-serialize; otherwise string
        try:
            if isinstance(val, (dict, list)):
                return json.dumps(val)
            return str(val)
        except Exception:
            return str(val)

    return pattern.sub(repl, template)


class ImageSaveWithMetadata:
    def __init__(self):
        self.output_dir = folder_paths.output_directory

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "images": ("IMAGE", ),
                "path_and_filename": ("STRING", {"default": "%time", "multiline": False}),
                "extension": ((['png', 'jpeg', 'webp']),),
            },
            "optional": {
                "custom_string": ("STRING", {"default": '', "multiline": True}),
                "lossless_webp": ("BOOLEAN", {"default": True}),
                "quality_jpeg_or_webp": ("INT", {"default": 100, "min": 1, "max": 100}),
            },
            "hidden": {
                "prompt": "PROMPT",
            },
        }

    RETURN_TYPES = ()
    FUNCTION = "save_files"
    OUTPUT_NODE = True
    CATEGORY = "SATA_UtilityNode"

    def save_files(self, images, path_and_filename, extension, custom_string=None,
                   quality_jpeg_or_webp=100, lossless_webp=True, prompt=None):
        # Resolve placeholders first (uses prompt)
        try:
            resolved = resolve_placeholders(str(path_and_filename), prompt)
        except Exception:
            resolved = str(path_and_filename)

        # Normalize separators and split into directory + basename
        pa = resolved.replace('\\', '/').strip()
        pa_dir = os.path.dirname(pa)
        pa_base = os.path.basename(pa)
        # Remove extension from provided base if present; we'll use the extension input instead
        pa_base_noext = os.path.splitext(pa_base)[0]

        # Final filename and path
        filename = make_filename(pa_base_noext if pa_base_noext != '' else "%time")
        path = make_pathname(pa_dir)

        output_path = os.path.join(self.output_dir, path)

        if output_path.strip() != '':
            if not os.path.exists(output_path.strip()):
                print(f'The path `{output_path.strip()}` specified doesn\'t exist! Creating directory.')
                os.makedirs(output_path, exist_ok=True)

        comment_parts = []
        if custom_string:
            comment_parts.append(handle_whitespace(custom_string))
        if prompt is not None:
            try:
                prompt_text = json.dumps(prompt)
            except Exception:
                prompt_text = str(prompt)
            comment_parts.append(f"Prompt: {handle_whitespace(prompt_text)}")

        comment = "\n".join(comment_parts).strip()

        # Resolve any %node/field% placeholders in filename and path using prompt
        try:
            filename = resolve_placeholders(filename, prompt)
            path = resolve_placeholders(path, prompt)
        except Exception:
            # Best-effort: if resolution fails, continue with original templates
            pass

        filenames = self.save_images(images, output_path, filename, comment, extension,
                                     quality_jpeg_or_webp, lossless_webp, prompt)

        subfolder = os.path.normpath(path)
        ui_images = [ {"filename": fn, "subfolder": subfolder if subfolder != '.' else '', "type": 'output'} for fn in filenames ]
        return {"ui": {"images": ui_images}}

    def save_images(self, images, output_path, filename_prefix, comment, extension, quality_jpeg_or_webp, lossless_webp, prompt=None) -> list:
        img_count = 1
        paths = []

        # images is a torch tensor (B,H,W,C) or a list/iterable of such tensors
        try:
            import torch
            is_torch = True
        except Exception:
            is_torch = False

        # Normalize input to list of images
        imgs = None
        if is_torch and hasattr(images, 'ndim'):
            imgs = [images[i] for i in range(images.shape[0])] if images.ndim == 4 else [images]
        elif isinstance(images, (list, tuple)):
            imgs = images
        else:
            imgs = [images]

        def find_unique_name(base_name: str, ext: str) -> str:
            """Return a file name (with extension) that does not collide on disk. Uses _0001 style suffixes."""
            candidate = f"{base_name}.{ext}"
            candidate_path = os.path.join(output_path, candidate)
            if not os.path.exists(candidate_path):
                return candidate
            idx = 1
            while True:
                candidate = f"{base_name}_{idx:04d}.{ext}"
                candidate_path = os.path.join(output_path, candidate)
                if not os.path.exists(candidate_path):
                    return candidate
                idx += 1

        for image in imgs:
            # Convert to PIL Image
            if is_torch and hasattr(image, 'cpu'):
                i = 255. * image.cpu().numpy()
                img = Image.fromarray(np.clip(i, 0, 255).astype(np.uint8))
            else:
                # assume numpy array
                arr = np.array(image)
                if arr.dtype != np.uint8:
                    arr = np.clip(arr * 255.0, 0, 255).astype(np.uint8)
                img = Image.fromarray(arr)

            # Base filename (without extension)
            base_name = filename_prefix

            if extension == 'png':
                metadata = PngInfo()
                if comment:
                    metadata.add_text("parameters", comment)

                if prompt is not None:
                    try:
                        metadata.add_text("prompt", json.dumps(prompt))
                    except Exception:
                        metadata.add_text("prompt", str(prompt))

                    # No extra_pnginfo support: only include the prompt (handled above)

                outname = find_unique_name(base_name, 'png')
                img.save(os.path.join(output_path, outname), pnginfo=metadata, optimize=True)
            else:
                ext = extension
                if ext == 'jpeg':
                    ext_name = 'jpg'
                else:
                    ext_name = ext

                outname = find_unique_name(base_name, ext_name)
                file_path = os.path.join(output_path, outname)
                img.save(file_path, optimize=True, quality=quality_jpeg_or_webp, lossless=lossless_webp if ext_name=='webp' else False)

                # Insert EXIF user comment with our metadata
                if comment:
                    try:
                        exif_bytes = piexif.dump({
                            "Exif": {
                                piexif.ExifIFD.UserComment: piexif.helper.UserComment.dump(comment, encoding="unicode")
                            },
                        })
                        piexif.insert(exif_bytes, file_path)
                    except Exception:
                        # piexif may fail for some formats; ignore silently
                        pass

            paths.append(outname)
            img_count += 1

        return paths
