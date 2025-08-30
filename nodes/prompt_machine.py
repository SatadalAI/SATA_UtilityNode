import os
import csv
import folder_paths

class Prompt_Machine:
    CATEGORY = "Custom Nodes"
    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("positive", "negative")
    FUNCTION = "get_prompts"

    # Directory for CSVs
    prompts_dir = os.path.join(os.path.dirname(__file__), "..", "prompts")
    folder_paths.add_model_folder_path("sata_prompts", prompts_dir)

    @classmethod
    def list_csv_files(cls):
        """Find all available CSV files"""
        csv_files = []
        if os.path.exists(cls.prompts_dir):
            for f in os.listdir(cls.prompts_dir):
                if f.lower().endswith(".csv"):
                    csv_files.append(f)
        return csv_files or ["prompts.csv"]

    @classmethod
    def load_csv(cls, csv_file):
        """Read CSV -> return mapping + options"""
        mapping = {}
        options = []
        csv_path = os.path.join(cls.prompts_dir, csv_file)

        if os.path.exists(csv_path):
            with open(csv_path, "r", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    name = (row.get("name") or "").strip()
                    positive = (row.get("positive") or "").strip()
                    negative = (row.get("negative") or "").strip()
                    if name:
                        options.append(name)
                        mapping[name] = (positive, negative)

        if not options:
            options = ["None"]
            mapping["None"] = ("", "")

        return mapping, options

    @classmethod
    def INPUT_TYPES(cls):
        csv_files = cls.list_csv_files()
        # Start with first CSV
        default_csv = csv_files[0]
        _, options = cls.load_csv(default_csv)

        return {
            "required": {
                "csv_file": (csv_files, {"default": default_csv}),
                "selection": (options, {"default": options[0]}),
            }
        }

    @classmethod
    def refresh(cls, csv_file=None, **kwargs):
        """Called when csv_file changes -> updates selection dropdown"""
        mapping, options = cls.load_csv(csv_file or cls.list_csv_files()[0])
        return {
            "selection": (options, {"default": options[0]})
        }

    def get_prompts(self, csv_file, selection):
        mapping, options = self.load_csv(csv_file)

        # Fix invalid selection
        if selection not in mapping:
            selection = options[0]

        positive, negative = mapping.get(selection, ("", ""))
        return (positive, negative)