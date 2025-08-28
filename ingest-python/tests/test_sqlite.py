from pathlib import Path

from telemon.db.sqlite import connect, init_db, insert_observations
from telemon.models import Observation


def test_insert_and_read(tmp_path: Path):
    db_path = tmp_path / "t.db"
    init_db(db_path)

    obs = Observation(
        ts_utc="2025-08-28T07:00:00Z",
        service_id="vodafone",
        iso2="GB",
        metric="report_count",
        value=42,
        source="downdetector",
        confidence=0.7,
        raw={"k": "v"},
    )
    inserted = insert_observations(db_path, [obs])
    assert inserted == 1

    con = connect(db_path)
    row = con.execute("SELECT service_id, iso2, value FROM observations").fetchone()
    assert row == ("vodafone", "GB", 42)
