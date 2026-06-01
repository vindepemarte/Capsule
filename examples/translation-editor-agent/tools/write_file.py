from __future__ import annotations

import os


def write_text_file(translated_text: str) -> dict[str, str]:
    path = "translation.txt"
    # Make sure we write cleanly
    with open(path, "w", encoding="utf-8") as f:
        f.write(translated_text)
    return {"filepath": os.path.abspath(path)}
