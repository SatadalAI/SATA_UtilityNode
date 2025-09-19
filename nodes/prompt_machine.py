# prompt_machine_node.py
import os
import csv
from server import PromptServer
from aiohttp import web

# Directory for CSV files (adjust if needed)
CSV_DIR = os.path.join(os.path.dirname(__file__), "..", "prompts")

def list_csv_files():
    try:
        return sorted([f for f in os.listdir(CSV_DIR) if f.endswith(".csv")])
    except Exception as e:
        print(f"[PromptMachine] list_csv_files error: {e}")
        return []

def read_names_from_csv(filename):
    """Return list of names (stripped) from CSV's 'name' column."""
    if not filename:
        return []
    path = os.path.join(CSV_DIR, filename)
    if not os.path.exists(path):
        print(f"[PromptMachine] CSV not found: {path}")
        return []
    try:
        with open(path, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            if not reader.fieldnames:
                print(f"[PromptMachine] CSV has no header: {filename}")
                return []
            field_map = {fn.strip().lower(): fn for fn in reader.fieldnames}
            if "name" not in field_map:
                print(f"[PromptMachine] CSV missing 'name' column: {filename}")
                return []
            name_field = field_map["name"]
            names = []
            for row in reader:
                raw = row.get(name_field)
                if raw is None:
                    continue
                val = raw.strip()
                if val:
                    names.append(val)
            return names
    except Exception as e:
        print(f"[PromptMachine] read_names_from_csv error for {filename}: {e}")
        return []

def read_prompt_row(csv_file, name):
    """Return (positive, negative, note) for a given csv_file and name.
       Matching is whitespace-trimmed and exact on content (case-sensitive by default)."""
    if not csv_file or csv_file == "None" or not name or name == "None":
        return ("", "", "")
    path = os.path.join(CSV_DIR, csv_file)
    if not os.path.exists(path):
        print(f"[PromptMachine] CSV file not found: {path}")
        return ("", "", "")
    try:
        with open(path, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            if not reader.fieldnames:
                print(f"[PromptMachine] CSV has no header: {csv_file}")
                return ("", "", "")
            field_map = {fn.strip().lower(): fn for fn in reader.fieldnames}
            if "name" not in field_map:
                print(f"[PromptMachine] 'name' column missing in CSV: {csv_file}")
                return ("", "", "")
            name_field = field_map["name"]
            pos_field = field_map.get("positive", "positive")
            neg_field = field_map.get("negative", "negative")
            note_field = field_map.get("note", "note")

            target = name.strip()
            for row in reader:
                cell = row.get(name_field)
                if cell is None:
                    continue
                if cell.strip() == target:
                    pos = (row.get(pos_field) or "").strip()
                    neg = (row.get(neg_field) or "").strip()
                    note = (row.get(note_field) or "").strip()
                    return (pos, neg, note)
    except Exception as e:
        print(f"[PromptMachine] read_prompt_row error for {csv_file}, {name}: {e}")
    return ("", "", "")


class Prompt_Machine:
    """
    NOTE: name is a free STRING (not a static dropdown) to avoid 'Value not in list' validation errors.
    The frontend helper will still provide dropdown-like selection and write the chosen name into this STRING.
    """
    @classmethod
    def INPUT_TYPES(cls):
        csvs = list_csv_files()
        default_csv = csvs[0] if csvs else "None"
        # default_name set to first name of default CSV if available
        names = read_names_from_csv(default_csv) if default_csv != "None" else []
        default_name = names[0] if names else "None"

        return {
            "required": {
                "csv_file": (csvs if csvs else ["None"], {
                    "default": default_csv,
                    # not using get_dynamic_inputs; frontend helper writes the STRING
                    "refresh": False,
                }),
                # make 'name' a free text field (STRING) — avoids list validation problems
                "name": ("STRING", {"default": default_name}),
            }
        }

    RETURN_TYPES = ("STRING", "STRING", "STRING")
    RETURN_NAMES = ("positive", "negative", "note")
    FUNCTION = "get_prompts"
    CATEGORY = "SATA_UtilityNode"

    def get_prompts(self, csv_file, name):
        print(f"[PromptMachine] get_prompts - csv_file={csv_file}, name={name}")
        pos, neg, note = read_prompt_row(csv_file, name)
        print(f"[PromptMachine] get_prompts -> pos_len={len(pos)}, neg_len={len(neg)}, note_len={len(note)}")
        return (pos, neg, note)


# ---------------- REST API ----------------

@PromptServer.instance.routes.get("/sata/prompt_machine/csvs")
async def list_csvs(request):
    """Return all available CSV files"""
    files = list_csv_files()
    return web.json_response({"csvs": files})


@PromptServer.instance.routes.get("/sata/prompt_machine/names")
async def list_names(request):
    """Return names from a selected CSV"""
    csv_file = request.query.get("csv")
    names = read_names_from_csv(csv_file) if csv_file else []
    return web.json_response({"names": names})


@PromptServer.instance.routes.get("/sata/prompt_machine/get")
async def get_prompt(request):
    """
    Return the prompt triple for immediate frontend consumption.
    Example: /sata/prompt_machine/get?csv=characters.csv&name=Bob
    """
    csv_file = request.query.get("csv")
    name = request.query.get("name")
    pos, neg, note = read_prompt_row(csv_file, name)
    return web.json_response({"positive": pos, "negative": neg, "note": note})