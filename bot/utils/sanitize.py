import re


def sanitize_title(title: str) -> str:
    value = re.sub(r"[^\w\s-]", "", title, flags=re.UNICODE)
    value = re.sub(r"\s+", " ", value).strip()
    if not value:
        return "note"
    return value[:80]


def build_note_filename(title: str, timestamp: str) -> str:
    safe_title = sanitize_title(title).replace(" ", "_")
    return f"{safe_title}_{timestamp}.md"
