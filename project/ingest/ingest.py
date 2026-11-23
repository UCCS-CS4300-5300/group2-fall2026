# This script converts the SRD into a bunch of smaller chunks and puts it into chunks.json

import re
from pathlib import Path
import json

DEFAULT_RULES_MAKRDOWN_FOLDER = Path(__file__).resolve().parent.parent / "local_data" / "dnd.srd.5.1-md"

def split_by_headings(text, file_title):
    stack = []            # [(level, title), ...]
    lines_buf = []
    out = []              # [(heading_path, body), ...]

    def flush():
        body = "\n".join(lines_buf).strip()
        if body:
            path = " > ".join([file_title] + [t for _, t in stack])
            out.append((path, body))
        lines_buf.clear()

    for line in text.splitlines():
        m = re.match(r"^(#{1,6})\s+(.*)", line)
        if m:
            flush()
            level = len(m.group(1))
            while stack and stack[-1][0] >= level:
                stack.pop()
            stack.append((level, m.group(2).strip()))
        else:
            lines_buf.append(line)
    flush()
    return out

def split_long(body, max_chars=3000):
    if len(body) <= max_chars:
        return [body]
    pieces, current = [], ""
    for para in body.split("\n\n"):
        if current and len(current) + len(para) > max_chars:
            pieces.append(current)
            current = ""
        current += para + "\n\n"
    if current.strip():
        pieces.append(current)
    return pieces

if __name__ == "__main__":
    chunks = []
    for path in Path(DEFAULT_RULES_MAKRDOWN_FOLDER).rglob("*.md"):
        if str(path).endswith("Legal.md"): # Don't chunk the "Legal.md" file. It's not needed
            continue
        text = path.read_text(encoding="utf-8")
        for heading_path, body in split_by_headings(text, path.stem):
            for piece in split_long(body):
                chunks.append({
                    "source": str(path),
                    "heading": heading_path,
                    "body": piece.strip(),
                })

    with open("chunks.json", "w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False, indent=2)