import os
import csv

class Prompt_Machine:
    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("positive", "negative")
    FUNCTION = "get_prompts"
    CATEGORY = "Custom Nodes"

    @classmethod
    def _load_csv(cls, csv_path):
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
        # Default CSV path = one level up (SATA_UtilityNode/prompts.csv)
        base_dir = os.path.dirname(os.path.dirname(__file__))
        default_csv = os.path.join(base_dir, "prompts.csv")

        # Load CSV once at UI build
        cls.options, cls.mapping = cls._load_csv(default_csv)

        return {
            "required": {
                "selection": (cls.options, ),
            },
            "optional": {
                "csv_file": ("STRING", {"default": default_csv}),
            }
        }

    def get_prompts(self, selection, csv_file=None):
        # Reload CSV if a different file is specified
        if csv_file and os.path.exists(csv_file) and csv_file != "":
            options, mapping = self._load_csv(csv_file)
        else:
            options, mapping = self.options, self.mapping

        positive, negative = mapping.get(selection, ("", ""))
        print(f"[Prompt_Machine] Selected: {selection}")
        print(f"  Positive: {positive}")
        print(f"  Negative: {negative}")
        return (str(positive), str(negative))