import os
import csv
from server import PromptServer

class Prompt_Machine:
    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("positive", "negative")
    FUNCTION = "get_prompts"
    CATEGORY = "Custom Nodes"

    # Keep track of last loaded CSV + options
    csv_cache = {}
    options = ["None"]
    mapping = {"None": ("", "")}

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

            print(f"[Prompt_Machine] Loaded {len(options)} entries.")
        else:
            print(f"[Prompt_Machine] ERROR: File not found: {csv_path}")

        if not options:
            options = ["None"]
            mapping = {"None": ("", "")}
            print("[Prompt_Machine] No valid entries, using default 'None'.")

        cls.csv_cache[csv_path] = (options, mapping)
        return options, mapping

    @classmethod
    def INPUT_TYPES(cls):
        # Register "sata_prompts" folder for CSVs
        base_dir = os.path.dirname(os.path.dirname(__file__))
        prompts_dir = os.path.join(base_dir, "prompts")
        os.makedirs(prompts_dir, exist_ok=True)

        # Default csv path
        default_csv = os.path.join(prompts_dir, "prompts.csv")

        # Load default if not yet cached
        if default_csv not in cls.csv_cache:
            cls.options, cls.mapping = cls._load_csv(default_csv)
        else:
            cls.options, cls.mapping = cls.csv_cache[default_csv]

        # Find available CSVs
        csv_files = [f for f in os.listdir(prompts_dir) if f.endswith(".csv")]
        csv_paths = [os.path.join(prompts_dir, f) for f in csv_files]

        return {
            "required": {
                "csv_file": (csv_paths, {"default": default_csv}),
                "selection": (cls.options, {"default": cls.options[0]}),
            }
        }

    def get_prompts(self, csv_file, selection):
        # Reload only if not cached
        if csv_file not in self.csv_cache:
            options, mapping = self._load_csv(csv_file)
        else:
            options, mapping = self.csv_cache[csv_file]

        # Make sure selection is valid
        if selection not in mapping:
            selection = options[0]

        positive, negative = mapping.get(selection, ("", ""))
        print(f"[Prompt_Machine] Row selected: {selection}")
        print(f"  Positive: {positive}")
        print(f"  Negative: {negative}")
        return (str(positive), str(negative))