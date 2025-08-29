import os
import csv

class Prompt_Machine:
    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("positive", "negative")
    FUNCTION = "get_prompts"
    CATEGORY = "Custom Nodes"

    @classmethod
    def _load_csv(cls):
        csv_path = os.path.join(os.path.dirname(__file__), "prompts.csv")
        options = []
        mapping = {}

        if os.path.exists(csv_path):
            with open(csv_path, "r", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    name = row.get("name", "").strip()
                    positive = row.get("positive", "").strip()
                    negative = row.get("negative", "").strip()
                    if name:
                        options.append(name)
                        mapping[name] = (positive, negative)

        if not options:
            options = ["None"]
            mapping["None"] = ("", "")

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
        return (positive, negative)