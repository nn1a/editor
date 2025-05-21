import bleach
import re
from bleach.css_sanitizer import CSSSanitizer
from bs4 import BeautifulSoup

ALLOWED_TAGS = [
    "p",
    "br",
    "strong",
    "b",
    "em",
    "i",
    "u",
    "ul",
    "ol",
    "li",
    "blockquote",
    "code",
    "pre",
    "a",
    "img",
    "h1",
    "h2",
    "h3",
    "table",
    "thead",
    "tbody",
    "tr",
    "td",
    "th",
    "abbr",
    "acronym",
    "span",
    "div",
    "hr",
    "h4",
    "h5",
    "h6",
    "tfoot",
    "col",
    "colgroup",
]

ALLOWED_ATTRIBUTES = {
    "*": ["style", "title", "class"],
    "a": ["href", "title", "target", "rel"],
    "img": ["src", "alt", "width", "height"],
    "table": ["border", "cellpadding", "cellspacing"],
    "td": ["colspan", "rowspan", "align", "valign"],
    "th": ["colspan", "rowspan", "align", "valign"],
    "col": ["span", "width", "style"],
    "colgroup": ["span", "style"],
    "span": ["style"],
    "div": ["style"],
    "p": ["style"],
}

ALLOWED_PROTOCOLS = ["http", "https", "mailto"]


ALLOWED_CSS_PROPERTIES = [
    "color",
    "font-weight",
    "font-style",
    "text-align",
    "text-decoration",
    "font-size",
    "font-family",
    "background-color",
    "margin",
    "padding",
    "border",
    "border-collapse",
    "width",
    "height",
    "vertical-align",
    "white-space",
    "border-radius",
    "line-height",
    "max-width",
    "min-width",
    "max-height",
    "min-height",
]


DANGEROUS_STYLE_PATTERNS = [
    r'url\s*\(\s*["\']?\s*javascript:',  # background:url(javascript:...)
    r"position\s*:\s*absolute\s*(!important)?;?",  # position:absolute
    r"display\s*:\s*none",  # display:none
    r"z-index\s*:\s*\d{3,}",  # z-index:99999
    r"width\s*:\s*\d{4,}px",  # width:9999px
    r"height\s*:\s*\d{4,}px",  # height:9999px
]


ALLOWED_CLASSES = [
    "PlaygroundEditorTheme__paragraph",
    "PlaygroundEditorTheme__tabNode",
]

css_sanitizer = CSSSanitizer(allowed_css_properties=ALLOWED_CSS_PROPERTIES)


def sanitize_classes(soup):
    for tag in soup.find_all(class_=True):
        original_classes = tag.get("class", [])
        safe_classes = [cls for cls in original_classes if cls in ALLOWED_CLASSES]
        if safe_classes:
            tag["class"] = safe_classes
        else:
            del tag["class"]


def sanitize_inline_styles(soup):
    for tag in soup.find_all(style=True):
        original_style = tag["style"]
        style_lines = [
            line.strip() for line in original_style.split(";") if line.strip()
        ]
        safe_style_lines = []

        for line in style_lines:
            if not any(
                re.search(pattern, line, re.IGNORECASE)
                for pattern in DANGEROUS_STYLE_PATTERNS
            ):
                safe_style_lines.append(line)

        if safe_style_lines:
            tag["style"] = "; ".join(safe_style_lines)
        else:
            del tag["style"]


def remove_data_uri_images(soup):
    for img_tag in soup.find_all("img"):
        src = img_tag.get("src", "")
        if src.lower().startswith("data:"):
            img_tag.decompose()


def sanitize_html(html: str) -> str:
    cleaned = bleach.clean(
        html,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        protocols=ALLOWED_PROTOCOLS,
        css_sanitizer=css_sanitizer,
        strip=True,
    )

    soup = BeautifulSoup(cleaned, "html.parser")

    remove_data_uri_images(soup)
    sanitize_classes(soup)
    sanitize_inline_styles(soup)
    cleaned = str(soup)

    cleaned = bleach.linkify(
        cleaned,
        callbacks=bleach.linkifier.DEFAULT_CALLBACKS,
        skip_tags=None,
        parse_email=False,
    )

    return cleaned
