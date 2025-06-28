from behave import when, then
import subprocess

@when('I run the bankcleanr config command')
def run_config(context):
    context.result = subprocess.run(['python', '-m', 'bankcleanr', 'config'], capture_output=True)

@then('the exit code is 0')
def check_exit(context):
    assert context.result.returncode == 0
