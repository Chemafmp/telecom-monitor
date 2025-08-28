from pathlib import Path

from telemon.ingest.downdetector import parse_report_count


def test_parse_report_count_from_fixture():
    html_path = Path(__file__).parent / "fixtures" / "downdetector_sample.html"
    html = html_path.read_text(encoding="utf-8")
    assert parse_report_count(html) == 42


def test_parse_report_count_empty():
    html = "<html><body></body></html>"
    assert parse_report_count(html) == 0
