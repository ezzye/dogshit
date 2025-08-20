import os
import backend.llm_adapter as llm_adapter


def after_scenario(context, scenario):
    try:
        prev = context.prev_llm_provider
    except AttributeError:
        return
    if prev is None:
        os.environ.pop("LLM_PROVIDER", None)
    else:
        os.environ["LLM_PROVIDER"] = prev
    llm_adapter._adapter_instances.clear()
    del context.prev_llm_provider
