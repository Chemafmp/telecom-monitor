from selectolax.parser import HTMLParser


def parse_report_count(html: str) -> int:
    """Extrae el número de reportes desde el HTML (simulado)."""
    tree = HTMLParser(html)
    node = tree.css_first(".report-count")
    if node is None:
        return 0
    return int(node.text().strip())
