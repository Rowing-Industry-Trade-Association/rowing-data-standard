"""Generate committed FIT fixtures from the sample sessions."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from rowing_data import write_fit
from rowing_data.model import RowingSession
from sample_sessions import gps_update_session, stroke_boundary_session

FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures"

FIXTURES: dict[str, Callable[[], RowingSession]] = {
    "stroke-boundary.fit": stroke_boundary_session,
    "gps-update.fit": gps_update_session,
}


def main() -> None:
    FIXTURE_DIR.mkdir(parents=True, exist_ok=True)
    for name, session in FIXTURES.items():
        write_fit(session(), FIXTURE_DIR / name)


if __name__ == "__main__":
    main()
