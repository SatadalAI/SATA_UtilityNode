import os
import csv
import logging

logging.basicConfig(level=logging.INFO)
_log = logging.getLogger("Prompt_Machine")

class Prompt_Machine:
    CATEGORY = "Custom Nodes"
    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("positive", "negative")
    FUNCTION = "get_prompts"

    # where CSVs live (folder next to the node folder)
    prompts_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "prompts"))
    os.makedirs(prompts_dir, exist_ok=True)

    # simple in-memory cache: { "filename.csv": {name: (pos,neg), ... } }
    mapping_cache = {}

    @classmethod
    def list_csv_files(cls):
        """Return list of CSV file basenames in prompts_dir"""
        try:
            files = [f for f in os.listdir(cls.prompts_dir) if f.lower().endswith(".csv")]
        except Exception:
            files = []
        return files or ["prompts.csv"]

    @classmethod
    def load_csv(cls, csv_file):
        """Load a CSV and return (options_list, mapping_dict)"""
        mapping = {}
        options = []
        if not csv_file:
            return ["None"], {"None": ("", "")}

        csv_path = os.path.join(cls.prompts_dir, csv_file)
        if os.path.exists(csv_path):
            _log.info(f"[Prompt_Machine] Loading CSV: {csv_path}")
            try:
                with open(csv_path, "r", encoding="utf-8-sig", newline="") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        name = (row.get("name") or "").strip()
                        positive = (row.get("positive") or "").strip()
                        negative = (row.get("negative") or "").strip()
                        if name:
                            options.append(name)
                            mapping[name] = (positive, negative)
            except Exception as e:
                _log.exception(f"[Prompt_Machine] Failed to read CSV '{csv_path}': {e}")

        if not options:
            options = ["None"]
            mapping = {"None": ("", "")}

        return options, mapping

    @classmethod
    def INPUT_TYPES(cls):
        """Initial UI build: show CSV files and default selection from the first CSV"""
        csv_files = cls.list_csv_files()
        default_csv = csv_files[0]
        options, mapping = cls.load_csv(default_csv)
        # cache for faster future loads
        cls.mapping_cache[default_csv] = mapping

        return {
            "required": {
                # csv_file shows available basenames (user picks one)
                "csv_file": (csv_files, {"default": default_csv}),
                # selection will be populated from the currently-loaded CSV
                "selection": (options, {"default": options[0]}),
            }
        }

    @classmethod
    def refresh_inputs(cls, csv_file=None, **kwargs):
        """
        IMPORTANT: ComfyUI calls refresh_inputs when a required/optional input changes.
        Here we rebuild 'selection' when csv_file changes.
        """
        csv_files = cls.list_csv_files()

        if not csv_file or csv_file not in csv_files:
            # file missing or not in list -> return available csvs and default selection from first file
            default_csv = csv_files[0]
            options, mapping = cls.load_csv(default_csv)
            cls.mapping_cache[default_csv] = mapping
            return {
                "required": {
                    "csv_file": (csv_files, {"default": default_csv}),
                    "selection": (options, {"default": options[0]}),
                }
            }

        # load the chosen csv (always reload fresh so changes are picked up)
        options, mapping = cls.load_csv(csv_file)
        cls.mapping_cache[csv_file] = mapping

        return {
            "required": {
                # keep the csv_file dropdown showing all CSVs but default to chosen file
                "csv_file": (csv_files, {"default": csv_file}),
                # update selection dropdown to new CSV options
                "selection": (options, {"default": options[0]}),
            }
        }

    def get_prompts(self, csv_file, selection):
        """Called during node execution; ensures mapping for csv_file exists then returns chosen row"""
        # ensure mapping cached
        if csv_file not in self.mapping_cache:
            # fallback load
            options, mapping = self.load_csv(csv_file)
            self.mapping_cache[csv_file] = mapping

        mapping = self.mapping_cache.get(csv_file, {})
        if selection not in mapping:
            # pick first available
            selection = next(iter(mapping.keys())) if mapping else "None"

        positive, negative = mapping.get(selection, ("", ""))
        _log.info(f"[Prompt_Machine] Selected: {selection}")
        _log.info(f"  Positive: {positive!r}")
        _log.info(f"  Negative: {negative!r}")

        # must return tuple matching RETURN_TYPES
        return (str(positive), str(negative))