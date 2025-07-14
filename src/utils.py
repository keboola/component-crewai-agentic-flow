import os
from pathlib import Path


def get_data_path(subpath: str) -> Path:
    base_path = Path(os.environ.get("KBC_DATADIR", "/data"))
    return base_path / subpath
