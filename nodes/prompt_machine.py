import os
import csv

class Prompt_Machine:
    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("positive", "negative")
    FUNCTION = "get_prompts"
    CATEGORY = "Custom Nodes"

    @classmethod
    def _load_csv(cls):
        # Go up one level from "nodes/" to "SATA_UtilityNode/"
        base_dir = os.path.dirname(os.path.dirname(__file__))
        csv_path = os.path.join(base_dir, "prompts.csv")

        options = []
        mapping = {}

        if os.path.exists(csv_path):
            print(f"[Prompt_Machine] Loading CSV from: {csv_path}")
            with open(csv_path, "r", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    name = row.get("name", "").strip()
                    positive = row.get("positive", "").strip()
                    negative = row.get("negative", "").strip()
                    if name:
                        options.append(name)
                        mapping[name] = (positive, negative)

            print(f"[Prompt_Machine] Loaded {len(options)} entries from CSV.")

        else:
            print(f"[Prompt_Machine] ERROR: CSV file not found at {csv_path}")

        if not options:
            options = ["None"]
            mapping["None"] = ("", "")
            print("[Prompt_Machine] No valid entries found, defaulting to 'None'.")

        return options, mapping

    @classmethod
    def INPUT_TYPES(cls):
        cls.options, cls.mapping = cls._load_csv()
        return {
            "required": {
                "selection": (cls.options, ),
            }
        }

    def get_prompts(self, selection):
        positive, negative = self.mapping.get(selection, ("", ""))
        print(f"[Prompt_Machine] Selected: {selection} -> Positive: {positive[:30]}..., Negative: {negative[:30]}...")
        return (positive, negative)