import os
import yaml
import dvc.api
from typing import Any, Optional

PARAMS_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "params.yaml")

def get_params(section: Optional[str] = None, default: Any = None) -> Any:
    """
    Mengambil parameter konfigurasi secara konsisten dari dvc.api atau params.yaml secara aman.
    Jika section diberikan, mengembalikan dictionary section tersebut (atau default jika tidak ada).
    """
    params = {}
    try:
        params = dvc.api.params_show()
    except Exception:
        if os.path.exists(PARAMS_FILE):
            try:
                with open(PARAMS_FILE, "r", encoding="utf-8") as f:
                    params = yaml.safe_load(f) or {}
            except Exception:
                params = {}

    if section:
        return params.get(section, default if default is not None else {})
    return params
