import os
import csv
import json
from server import PromptServer
from aiohttp import web

# Directory for Prompt files
PROMPT_DIR = os.path.join(os.path.dirname(__file__), "..", "prompt")

def list_prompt_files():
    try:
        if not os.path.exists(PROMPT_DIR):
            return []
        return sorted([f for f in os.listdir(PROMPT_DIR) if f.endswith(".csv") or f.endswith(".json")])
    except Exception as e:
        print(f"[PromptAutocomplete] list_prompt_files error: {e}")
        return []

def read_prompt_file(filename):
    """Read and parse a CSV or JSON file."""
    if not filename:
        return []
    path = os.path.join(PROMPT_DIR, filename)
    if not os.path.exists(path):
        print(f"[PromptAutocomplete] File not found: {path}")
        return []
    
    data = []
    try:
        if filename.endswith(".csv"):
            with open(path, "r", encoding="utf-8-sig") as f:
                reader = csv.reader(f)
                # Simple CSV parsing: treat first column as the value
                for row in reader:
                    if row:
                        data.append(row[0].strip())
        elif filename.endswith(".json"):
            with open(path, "r", encoding="utf-8-sig") as f:
                content = json.load(f)
                # Expecting a list of strings or objects with 'name'/'prompt'
                if isinstance(content, list):
                    for item in content:
                        if isinstance(item, str):
                            data.append(item)
                        elif isinstance(item, dict):
                            # Try to find a meaningful text field
                            val = item.get("prompt") or item.get("text") or item.get("name") or item.get("value")
                            if val:
                                data.append(str(val))
                elif isinstance(content, dict):
                     # If it's a dict, maybe keys or values are the prompts? 
                     # Let's assume keys are categories or names, and values are prompts if strings
                     for k, v in content.items():
                         if isinstance(v, str):
                             data.append(v)
                         elif isinstance(v, list):
                             # Flatten list values
                             data.extend([str(x) for x in v if isinstance(x, str)])

    except Exception as e:
        print(f"[PromptAutocomplete] Error reading {filename}: {e}")
        return []
        
    return data

class PromptAutocomplete:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "text": ("STRING", {"multiline": True, "dynamicPrompts": True}), 
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("text",)
    FUNCTION = "do_nothing"
    CATEGORY = "SATA_UtilityNode"

    def do_nothing(self, text):
        return (text,)

# ---------------- REST API ----------------

@PromptServer.instance.routes.get("/sata/autocomplete/list")
async def list_files(request):
    """Return all available prompt files"""
    files = list_prompt_files()
    return web.json_response({"files": files})

@PromptServer.instance.routes.get("/sata/autocomplete/get")
async def get_file_content(request):
    """Return content of a specific file"""
    filename = request.query.get("file")
    items = read_prompt_file(filename)
    return web.json_response({"items": items})
