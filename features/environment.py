import os
from bankcleanr.rules import regex

def after_scenario(context, scenario):
    if "_orig_key" in context.__dict__:
        if context._orig_key is None:
            os.environ.pop("OPENAI_API_KEY", None)
        else:
            os.environ["OPENAI_API_KEY"] = context._orig_key
        try:
            delattr(context, "_orig_key")
        except Exception:
            pass
    if hasattr(context, "heuristics_path"):
        regex.HEURISTICS_PATH = getattr(context, "orig_heuristics", regex.DATA_DIR / "heuristics.yml")
        regex.reload_patterns()
        delattr(context, "heuristics_path")
        if hasattr(context, "orig_heuristics"):
            delattr(context, "orig_heuristics")
