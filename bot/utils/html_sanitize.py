from html import escape
from html.parser import HTMLParser

_ALLOWED_TAGS = {"a", "b", "i"}


class _HTMLSanitizer(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.stack: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag not in _ALLOWED_TAGS:
            return

        if tag == "a":
            href = None
            for name, value in attrs:
                if name == "href" and value:
                    href = value
                    break
            if not href:
                return
            safe_href = escape(href, quote=True)
            self.parts.append(f"<a href=\"{safe_href}\">")
            self.stack.append(tag)
            return

        self.parts.append(f"<{tag}>")
        self.stack.append(tag)

    def handle_endtag(self, tag: str) -> None:
        if tag not in _ALLOWED_TAGS:
            return
        if not self.stack or self.stack[-1] != tag:
            return
        self.stack.pop()
        self.parts.append(f"</{tag}>")

    def handle_data(self, data: str) -> None:
        self.parts.append(escape(data))


def sanitize_html(text: str) -> str:
    sanitizer = _HTMLSanitizer()
    sanitizer.feed(text)
    sanitizer.close()
    for tag in reversed(sanitizer.stack):
        sanitizer.parts.append(f"</{tag}>")
    return "".join(sanitizer.parts)
