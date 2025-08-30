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

    # folder next to 'nodes' (custom_nodes/SATA_UtilityNode/prompts)
    prompts_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "prompts"))
    os.makedirs(prompts_dir, exist_ok=True)

    # cache keyed by full csv-path -> { name: (positive, negative), ... }
    mapping_cache = {}

    @classmethod
    def list_csv_files(cls):
        """Return list of absolute paths for CSV files in prompts_dir"""
        try:
            files = [
                os.path.join(cls.prompts_dir, f)
                for f in sorted(os.listdir(cls.prompts_dir))
                if f.lower().endswith(".csv")
            ]
        except Exception:
            files = []

        # keep at least one "prompts.csv" path so UI isn't empty
        if not files:
            files = [os.path.join(cls.prompts_dir, "prompts.csv")]
        return files

    @classmethod
    def load_csv(cls, csv_fullpath):
        """
        Read CSV (case-insensitive headers) -> return (options_list, mapping_dict)
        mapping: { name: (positive, negative) }
        """
        mapping = {}
        options = []

        if not csv_fullpath:
            return ["None"], {"None": ("", "")}

        csv_fullpath = os.path.abspath(csv_fullpath)

        if os.path.exists(csv_fullpath):
            _log.info(f"[Prompt_Machine] Loading CSV: {csv_fullpath}")
            try:
                with open(csv_fullpath, "r", encoding="utf-8-sig", newline="") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        if row is None:
                            continue
                        # normalize keys to lowercase, strip values
                        nrow = {}
                        for k, v in row.items():
                            if k is None:
                                continue
                            nrow[k.strip().lower()] = (v or "").strip()
                        name = nrow.get("name", "")
                        positive = nrow.get("positive", "")
                        negative = nrow.get("negative", "")
                        if name:
                            options.append(name)
                            mapping[name] = (positive, negative)
            except Exception as e:
                _log.exception(f"[Prompt_Machine] Failed to read CSV '{csv_fullpath}': {e}")
        else:
            _log.warning(f"[Prompt_Machine] CSV file does not exist: {csv_fullpath}")

        if not options:
            options = ["None"]
            mapping = {"None": ("", "")}

        return options, mapping

    @classmethod
    def INPUT_TYPES(cls):
        """
        Initial build: csv_file shows full absolute paths; selection is filled from the first CSV.
        """
        csv_paths = cls.list_csv_files()
        default_csv = csv_paths[0]
        options, mapping = cls.load_csv(default_csv)
        # cache initial file
        cls.mapping_cache[default_csv] = mapping

        # Show full paths in dropdown so selected value equals what refresh_inputs/get_prompts receive
        return {
            "required": {
                "csv_file": (csv_paths, {"default": default_csv}),
                "selection": (options, {"default": options[0]}),
            }
        }

    @classmethod
    def refresh_inputs(cls, csv_file=None, **kwargs):
        """
        Called by ComfyUI when an input changes. Rebuild 'selection' based on chosen csv_file.
        Using absolute paths for csv_file avoids mismatch between displayed value and passed value.
        """
        csv_paths = cls.list_csv_files()

        # If the passed csv_file is not in available list, fallback to first file
        if not csv_file or csv_file not in csv_paths:
            default_csv = csv_paths[0]
            options, mapping = cls.load_csv(default_csv)
            cls.mapping_cache[default_csv] = mapping
            return {
                "required": {
                    "csv_file": (csv_paths, {"default": default_csv}),
                    "selection": (options, {"default": options[0]}),
                }
            }

        # load chosen file fresh (so edits on disk are picked up)
        options, mapping = cls.load_csv(csv_file)
        cls.mapping_cache[csv_file] = mapping

        return {
            "required": {
                "csv_file": (csv_paths, {"default": csv_file}),
                "selection": (options, {"default": options[0]}),
            }
        }

    def get_prompts(self, csv_file, selection):
        """Execution-time: ensure mapping exists for csv_file and return selected prompts."""
        csv_file = os.path.abspath(csv_file) if csv_file else None

        if not csv_file:
            _log.warning("[Prompt_Machine] No csv_file provided; returning empty prompts.")
            return ("", "")

        if csv_file not in self.mapping_cache:
            options, mapping = self.load_csv(csv_file)
            self.mapping_cache[csv_file] = mapping
        else:
            mapping = self.mapping_cache[csv_file]

        if selection not in mapping:
            # pick first available name if selection invalid
            selection = next(iter(mapping.keys())) if mapping else "None"

        positive, negative = mapping.get(selection, ("", ""))
        _log.info(f"[Prompt_Machine] Selected: {selection}")
        _log.info(f"  Positive: {positive!r}")
        _log.info(f"  Negative: {negative!r}")

        return (str(positive), str(negative))