import os
import csv

class Prompt_Machine:
    def __init__(self):
        # Load CSV once during node init
        self.csv_path = os.path.join(os.path.dirname(__file__), "prompts.csv")
        self.options = []
        self.mapping = {}

        if os.path.exists(self.csv_path):
            with open(self.csv_path, "r", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    name = row.get("name", "").strip()
                    positive = row.get("positive", "").strip()
                    negative = row.get("negative", "").strip()
                    if name:
                        self.options.append(name)
                        self.mapping[name] = (positive, negative)

        # fallback if csv missing
        if not self.options:
            self.options = ["None"]
            self.mapping["None"] = ("", "")

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "selection": (cls().options, ),
            }
        }

    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("positive", "negative")
    FUNCTION = "get_prompts"
    CATEGORY = "Custom Nodes"

    def get_prompts(self, selection):
        positive, negative = self.mapping.get(selection, ("", ""))
        return (positive, negative)