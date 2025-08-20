import os
from behave import given, when, then
import backend.llm_adapter as llm_adapter


@given('the environment variable LLM_PROVIDER is set to "{provider}"')
def set_provider(context, provider):
    context.prev_llm_provider = os.environ.get("LLM_PROVIDER")
    os.environ["LLM_PROVIDER"] = provider
    llm_adapter._adapter_instances.clear()


@when("requesting an LLM adapter")
def request_adapter(context):
    context.adapter = llm_adapter.get_adapter()


@then('the adapter type is "{cls_name}"')
def check_adapter_type(context, cls_name):
    cls = getattr(llm_adapter, cls_name)
    assert isinstance(context.adapter, cls)


@then("the environment variable LLM_PROVIDER is unset")
def check_provider_unset(context):
    assert "LLM_PROVIDER" not in os.environ
