from pathlib import Path

import anyio

from telemon.ingest.downdetector import run


async def fake_fetch(_url: str) -> str:
    # Simula una respuesta HTML parecida a la del fixture del Día 2
    return "<html><div class='report-count'>17</div></html>"


def test_run_inserts_row(tmp_path: Path):
    db_path = tmp_path / "t.db"
    # Ejecuta run con fetch fake (sin red) y sin URL real
    anyio.run(
        run,
        "vodafone",
        "gb",
        str(db_path),
        None,
        None,
        fake_fetch,  # inyección
    )

    # Comprueba el contenido
    import sqlite3

    con = sqlite3.connect(db_path)
    row = con.execute("SELECT service_id, iso2, metric, value, source FROM observations").fetchone()
    assert row == ("vodafone", "GB", "report_count", 17, "downdetector")
