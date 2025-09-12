import os
import csv
from server import PromptServer
from aiohttp import web

CSV_DIR = os.path.join(os.path.dirname(__file__), "..", "prompts")

def list_csv_files():
    return sorted([f for f in os.listdir(CSV_DIR) if f.endswith(".csv")])

def read_names_from_csv(filename):
    path = os.path.join(CSV_DIR, filename)
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            return []
        field_map = {fn.strip().lower(): fn for fn in reader.fieldnames}
        if "name" not in field_map:
            return []
        name_field = field_map["name"]
        return [row[name_field] for row in reader if row.get(name_field)]

class Prompt_Machine:
    def __init__(self):
        csvs = list_csv_files()
        if csvs:
            self.default_csv = csvs[0]
            names = read_names_from_csv(self.default_csv)
            self.default_name = names[0] if names else "None"
        else:
            self.default_csv = "None"
            self.default_name = "None"

    @classmethod
    def INPUT_TYPES(cls):
        csvs = list_csv_files()
        default_csv = csvs[0] if csvs else "None"
        names = read_names_from_csv(default_csv) if csvs else []
        default_name = names[0] if names else "None"

        return {
            "required": {
                "csv_file": (csvs if csvs else ["None"], {"default": default_csv}),
                "name": (names if names else ["None"], {"default": default_name}),
            }
        }

    RETURN_TYPES = ("STRING", "STRING", "STRING")
    RETURN_NAMES = ("positive", "negative", "note")
    FUNCTION = "get_prompts"
    CATEGORY = "SATA_UtilityNode"

    def get_prompts(self, csv_file, name):
        if csv_file == "None" or name == "None":
            return ("", "", "null")
        path = os.path.join(CSV_DIR, csv_file)
        if not os.path.exists(path):
            print(f"[PromptMachine] CSV file not found: {path}")
            return ("", "", "null")
        with open(path, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            if not reader.fieldnames:
                print(f"[PromptMachine] CSV has no header: {csv_file}")
                return ("", "", "null")
            print(f"[PromptMachine] CSV header in {csv_file}: {reader.fieldnames}")
            field_map = {fn.strip().lower(): fn for fn in reader.fieldnames}
            if "name" not in field_map:
                print(f"[PromptMachine] 'name' column missing in CSV: {csv_file}")
                return ("", "", "null")
            name_field = field_map["name"]
            pos_field = field_map.get("positive", "positive")
            neg_field = field_map.get("negative", "negative")
            note_field = field_map.get("note", "note")
            for row in reader:
                if row.get(name_field) == name:
                    return (row.get(pos_field, ""), row.get(neg_field, ""), row.get(note_field, ""))
        return ("", "", "","null")


# REST endpoints for frontend refresh
@PromptServer.instance.routes.get("/sata/prompt_machine/csvs")
async def list_csvs(request):
    return web.json_response({"csvs": list_csv_files()})


@PromptServer.instance.routes.get("/sata/prompt_machine/names")
async def list_names(request):
    csv_file = request.query.get("csv")
    return web.json_response({"names": read_names_from_csv(csv_file)} if csv_file else {"names": []})
