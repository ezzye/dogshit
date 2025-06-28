GLOBAL_DISCLAIMER = (
    "This tool automates the categorisation of your personal bank transactions.\n"
    "It is not regulated financial advice. Results may be incomplete or inaccurate.\n"
    "All processing occurs on this computer; only transaction descriptions are sent to the language-model provider you choose.\n"
    "Use at your own risk. Always verify recommendations with the original supplier or your bank before cancelling any service."
)

def get_disclaimer() -> str:
    """Return the global disclaimer text."""
    return GLOBAL_DISCLAIMER
