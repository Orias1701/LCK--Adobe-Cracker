import logging
import re, os
import pandas as pd
import json, csv, openpyxl

from typing import Dict, List, Any, Tuple

def readJson(path: str) -> Any:
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def writeJson(data: Any, path: str, indent: int = 2) -> None:
    dirPath = os.path.dirname(path)
    if dirPath: os.makedirs(dirPath, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=indent, ensure_ascii=False)