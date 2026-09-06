import os
import re
from pathlib import Path
from typing import List, Dict, Any

COMPLEMENTARY_PATTERNS = ("mmproj", "mtp-", "-mtp", "draft", "imatrix")


def _is_complementary(filename: str) -> bool:
    name = filename.lower()
    return any(p in name for p in COMPLEMENTARY_PATTERNS)


def _detect_quantization(filename: str) -> str:
    m = re.search(r"(MXFP4|Q\d[A-Z0-9_]+)", filename)
    return m.group(1) if m else "unknown"


def scan_models(root_dir: str) -> List[Dict[str, Any]]:
    root_path = Path(root_dir)
    groups: Dict[str, Dict[str, Any]] = {}
    if not root_path.exists():
        return []
    for path in sorted(root_path.rglob("*.gguf")):
        filename = path.name
        if _is_complementary(filename):
            key = path.parent.as_posix()
            group = groups.setdefault(key, {"dir": str(path.parent), "files": {}})
            low = filename.lower()
            if "mmproj" in low:
                group["files"]["mmproj"] = str(path.absolute())
            elif "mtp" in low or "draft" in low:
                group["files"]["mtp_draft"] = str(path.absolute())
            elif "imatrix" in low:
                group["files"]["imatrix"] = str(path.absolute())
            continue
        key = path.parent.as_posix()
        group = groups.setdefault(key, {"dir": str(path.parent), "files": {}})
        prev = group["files"].get("main")
        if prev is None or path.stat().st_size > Path(prev).stat().st_size:
            group["files"]["main"] = str(path.absolute())
    models: List[Dict[str, Any]] = []
    for key, group in sorted(groups.items()):
        files = group.get("files", {})
        main = files.get("main")
        if not main:
            continue
        main_path = Path(main)
        size_gb = round(main_path.stat().st_size / (1024 ** 3), 2)
        models.append(
            {
                "name": main_path.stem,
                "path": str(main_path.absolute()),
                "size": main_path.stat().st_size,
                "size_gb": size_gb,
                "quantization": _detect_quantization(main_path.name),
                "dir": group.get("dir", ""),
                "mmproj": files.get("mmproj"),
                "mtp_draft": files.get("mtp_draft"),
                "imatrix": files.get("imatrix"),
                "has_mmproj": bool(files.get("mmproj")),
                "has_mtp": bool(files.get("mtp_draft")),
            }
        )
    return models
