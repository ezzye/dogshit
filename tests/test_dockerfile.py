from pathlib import Path
import re


def test_api_dockerfile_copies_data():
    dockerfile = Path("Dockerfile").read_text()
    assert re.search(r"^COPY\s+data\s+\.\/data\s*$", dockerfile, re.MULTILINE), (
        "Dockerfile must copy the data directory so taxonomy files are available in the API container"
    )
