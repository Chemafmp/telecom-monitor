from __future__ import annotations

import json
import os
import re
from typing import Callable

import anyio
import httpx
from selectolax.parser import HTMLParser

from telemon.db.sqlite import init_db, insert_observations
from telemon.models import Observation

# --- Config ---
DEFAULT_UA = os.environ.get("TELEMON_UA", "telemon/0.1 (+learning-project)")
RATE_LIMIT_MS = int(os.environ.get("TELEMON_RATE_LIMIT_MS", "1000"))  # 1 req/seg por defecto
RETRY_STATUS = {429, 500, 502, 503, 504}

# Nota ética/legal
# Día 3 permite una prueba manual. Respeta robots.txt/TOS del sitio real que consultes.
# Este código no fija el selector definitivo de Downdetector (puede cambiar).
# Usa la CLI con un HTML local (--from-file) o un endpoint tuyo de pruebas.


def _rate_limit_delay() -> float:
    return RATE_LIMIT_MS / 1000.0


async def fetch(url: str, *, headers: dict | None = None, timeout: float = 10.0) -> str:
    """
    Fetch con rate-limit y backoff exponencial ante errores transitorios.
    """
    await anyio.sleep(_rate_limit_delay())  # simple rate-limit
    attempt = 0
    backoff = 0.8  # segundos, se duplicará
    last_exc: Exception | None = None
    async with httpx.AsyncClient(
        timeout=timeout, headers=headers or {"User-Agent": DEFAULT_UA}
    ) as client:
        while attempt < 5:
            try:
                r = await client.get(url)
                if r.status_code in RETRY_STATUS:
                    raise httpx.HTTPStatusError(
                        f"Retryable status: {r.status_code}", request=r.request, response=r
                    )
                r.raise_for_status()
                return r.text
            except (httpx.RequestError, httpx.HTTPStatusError) as exc:
                last_exc = exc
                attempt += 1
                await anyio.sleep(backoff)
                backoff *= 2
        # agotados los intentos
        if last_exc:
            raise last_exc
        raise RuntimeError("fetch failed without exception")


# --------- Parsers (simples / robustos) ---------
def parse_report_count(html: str) -> int:
    """
    Intenta extraer un número 'report_count' de forma defensiva.
    1) Busca un nodo con clase .report-count (nuestro fixture del Día 2).
    2) Si no aparece, intenta un fallback: primera cifra grande en el documento.
    """
    tree = HTMLParser(html)

    node = tree.css_first(".report-count")
    if node:
        text = (node.text() or "").strip()
        try:
            return int(text)
        except ValueError:
            pass

    # Fallback: primera cifra con 1-6 dígitos (evita números enormes tipo timestamps)
    m = re.search(r"\b(\d{1,6})\b", tree.text() or "")
    if m:
        try:
            return int(m.group(1))
        except ValueError:
            return 0
    return 0


def build_observation(
    service: str, country: str, count: int, *, raw: dict | None = None
) -> Observation:
    return Observation(
        ts_utc=Observation.now_iso(),
        service_id=service,
        iso2=country.upper(),
        metric="report_count",
        value=count,
        source="downdetector",
        confidence=0.6,
        raw=raw,
    )


# --------- CLI runner ---------
async def run(
    service: str,
    country: str,
    db_path: str = "telemon.db",
    url: str | None = None,
    from_file: str | None = None,
    fetcher: Callable[[str], str] | None = None,
) -> None:
    """
    Ejecuta el flujo completo:
      - lee HTML desde URL o archivo
      - parsea el report_count
      - crea Observation
      - inserta en SQLite
    'fetcher' se usa para tests (inyectar función fake).
    """
    init_db(db_path)

    if from_file:
        html = open(from_file, "r", encoding="utf-8").read()
    else:
        # Permite modo test si hay fetcher aunque no haya URL real
        if url is None and fetcher is None:
            raise SystemExit(
                "Error: debes pasar --url <http...> o --from-file <ruta.html> (o inyectar fetcher en tests)."
            )
        if fetcher is None:
            html = await fetch(url)  # type: ignore[arg-type]
        else:
            html = await fetcher(url or "")

    count = parse_report_count(html)
    obs = build_observation(service, country, count, raw={"preview": html[:300]})
    inserted = insert_observations(db_path, [obs])

    summary = {
        "ts_utc": obs.ts_utc,
        "service_id": obs.service_id,
        "iso2": obs.iso2,
        "value": obs.value,
    }
    print(f"OK: inserted={inserted} obs={json.dumps(summary, ensure_ascii=False)}")


if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser(description="Telemon Downdetector Ingest")
    p.add_argument("--service", required=True, help="p.ej. vodafone")
    p.add_argument("--country", required=True, help="p.ej. gb")
    p.add_argument("--db", default="telemon.db")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--url", help="URL de prueba (respeta TOS/robots)")
    g.add_argument("--from-file", help="HTML local para pruebas offline")
    args = p.parse_args()
    anyio.run(run, args.service, args.country, args.db, args.url, args.from_file)
