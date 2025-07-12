import os

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
