import json
from typing import Any


def json_encode(value: Any) -> str:
    return json.dumps(value, sort_keys=True, indent=4, default=str).replace("</", "<\\/")
