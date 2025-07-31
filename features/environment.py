import os
import urllib.request
import importlib
from bankcleanr.rules import regex, db_store

ORIG_HEURISTICS = db_store.HEURISTICS_PATH.read_text()


def before_scenario(context, scenario):
    context._orig_auto_confirm = os.getenv("BANKCLEANR_AUTO_CONFIRM")
    os.environ["BANKCLEANR_AUTO_CONFIRM"] = ""

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
        db_store.HEURISTICS_PATH = getattr(
            context, "orig_heuristics", db_store.DATA_DIR / "heuristics.yml"
        )
        db_store.HEURISTICS_PATH.write_text(ORIG_HEURISTICS)
        importlib.reload(db_store)
        regex.reload_patterns()
        delattr(context, "heuristics_path")
        if hasattr(context, "orig_heuristics"):
            delattr(context, "orig_heuristics")
    if hasattr(context, "_orig_auto_confirm"):
        orig = getattr(context, "_orig_auto_confirm", None)
        if orig is None:
            os.environ.pop("BANKCLEANR_AUTO_CONFIRM", None)
        else:
            os.environ["BANKCLEANR_AUTO_CONFIRM"] = orig
        try:
            delattr(context, "_orig_auto_confirm")
        except AttributeError:
            pass
    try:
        orig = getattr(context, "_orig_backend_url")
    except Exception:
        orig = None
    else:
        if orig is None:
            os.environ.pop("BANKCLEANR_BACKEND_URL", None)
        else:
            os.environ["BANKCLEANR_BACKEND_URL"] = orig
        try:
            delattr(context, "_orig_backend_url")
        except Exception:
            pass
    try:
        orig = getattr(context, "_orig_backend_token")
    except Exception:
        orig = None
    else:
        if orig is None:
            os.environ.pop("BANKCLEANR_BACKEND_TOKEN", None)
        else:
            os.environ["BANKCLEANR_BACKEND_TOKEN"] = orig
        try:
            delattr(context, "_orig_backend_token")
        except Exception:
            pass
    try:
        orig = getattr(context, "_orig_urlopen")
    except Exception:
        pass
    else:
        urllib.request.urlopen = orig
        try:
            delattr(context, "_orig_urlopen")
        except Exception:
            pass
    try:
        db_file = getattr(context, "db_file")
    except Exception:
        db_file = None
    if db_file is not None:
        try:
            os.unlink(db_file)
        except Exception:
            pass
        try:
            orig = getattr(context, "_orig_app_env")
        except Exception:
            orig = None
        else:
            if orig is None:
                os.environ.pop("APP_ENV", None)
            else:
                os.environ["APP_ENV"] = orig
            try:
                delattr(context, "_orig_app_env")
            except Exception:
                pass
        importlib.reload(db_store)
        regex.reload_patterns()
        try:
            delattr(context, "db_file")
        except Exception:
            pass
