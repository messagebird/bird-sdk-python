"""Check that both public distribution formats contain the generated models."""

from pathlib import Path
from runpy import run_path
from tarfile import open as open_tar
from zipfile import ZipFile


dist = Path("dist")
version = run_path("src/bird/_version.py")["__version__"]
wheel = dist / f"messagebird_sdk-{version}-py3-none-any.whl"
sdist = dist / f"messagebird_sdk-{version}.tar.gz"

with ZipFile(wheel) as archive:
    assert "bird/_generated.py" in archive.namelist(), "wheel omits bird/_generated.py"

with open_tar(sdist, "r:gz") as archive:
    assert any(name.endswith("/src/bird/_generated.py") for name in archive.getnames()), (
        "sdist omits src/bird/_generated.py"
    )
