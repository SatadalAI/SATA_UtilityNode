import os
import csv
import logging
from aiohttp import web
from server import PromptServer

log = logging.getLogger("Prompt_Machine")
logging.basicConfig(level=logging.INFO)

# --- paths ---
# __file__ is inside .../custom_nodes/SATA_UtilityNode/nodes/
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PROMPTS_DIR = os.path.join(BASE_DIR, "prompts")
os.makedirs(PROMPTS_DIR, exist_ok=True)

DEFAULT_CSV = "prompts.csv"

def list_csv_files():
    try:
        files = sorted([f for f in os.listdir(PROMPTS_DIR) if f.lower().endswith(".csv")])
        if not files:
            # ensure at least default name exists (user can add file later)
            return [DEFAULT_CSV]
        return files
    except Exception as e:
        log.exception("[Prompt_Machine] list_csv_files error")
        return [DEFAULT_CSV]

def load_csv_map(csv_name):
    """
    csv_name: basename like 'prompts.csv'
    returns: (names_list, mapping_dict, full_path)
      mapping_dict: { name: (positive, negative) }
    """
    csv_name = os.path.basename(csv_name) if csv_name else DEFAULT_CSV
    path = os.path.join(PROMPTS_DIR, csv_name)
    names = []
    mapping = {}

    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8-sig", newline="") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if not row:
                        continue
                    # normalize headers to lowercase to accept Name/NAME/name
                    nrow = { (k or "").strip().lower(): (v or "").strip() for k,v in row.items() if k is not None }
                    name = nrow.get("name", "")
                    pos = nrow.get("positive", "")
                    neg = nrow.get("negative", "")
                    if name:
                        names.append(name)
                        mapping[name] = (pos, neg)
        except Exception as e:
            log.exception(f"[Prompt_Machine] Failed to read CSV '{path}'")
    else:
        log.debug(f"[Prompt_Machine] CSV not found: {path}")

    if not names:
        names = ["None"]
        mapping = {"None": ("", "")}

    return names, mapping, path

# --- HTTP routes: register multiple common endpoints so the JS discovery works ---
try:
    routes = PromptServer.instance.routes

    @routes.get("/sata/prompt_machine/csvs")
    @routes.get("/custom/SATA_UtilityNode/prompt_machine/csvs")
    @routes.get("/custom/SATA_UtilityNode/list_csv")
    async def _list_csvs(request):
        csvs = list_csv_files()
        log.info(f"[Prompt_Machine] _list_csvs -> {csvs}")
        return web.json_response({"items": csvs})

    @routes.get("/sata/prompt_machine/names")
    @routes.get("/custom/SATA_UtilityNode/prompt_machine/names")
    @routes.get("/custom/SATA_UtilityNode/list_names")
    async def _list_names(request):
        csv_name = request.query.get("csv") or DEFAULT_CSV
        names, mapping, path = load_csv_map(csv_name)
        log.info(f"[Prompt_Machine] _list_names served for: {csv_name} (path: {path}) -> {len(names)} names")
        return web.json_response({"items": names})
except Exception as e:
    log.exception("[Prompt_Machine] Route registration failed")

# --- Node class ---
class Prompt_Machine:
    CATEGORY = "Custom Nodes"
    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("positive", "negative")
    FUNCTION = "get_prompts"

    @classmethod
    def INPUT_TYPES(cls):
        csvs = list_csv_files()
        default_csv = csvs[0] if csvs else DEFAULT_CSV
        names, _, _ = load_csv_map(default_csv)
        # ensure non-empty
        if not names:
            names = ["None"]
        return {
            "required": {
                "csv_file": (csvs, {"default": default_csv}),
                "name": (names, {"default": names[0]}),
            }
        }

    def get_prompts(self, csv_file, name):
        names, mapping, path = load_csv_map(csv_file)
        if name not in mapping and names:
            name = names[0]
        positive, negative = mapping.get(name, ("", ""))
        log.info(f"[Prompt_Machine] Executing: csv={csv_file} name={name}")
        log.info(f"  positive: {repr(positive)}")
        log.info(f"  negative: {repr(negative)}")
        # must return a tuple of strings
        return (str(positive), str(negative))


# register node
NODE_CLASS_MAPPINGS = {
    "Prompt_Machine": Prompt_Machine
}
NODE_DISPLAY_NAME_MAPPINGS = {
    "Prompt_Machine": "Prompt Machine"
}