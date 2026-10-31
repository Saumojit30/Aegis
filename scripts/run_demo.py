"""One-command offline clinician demo runner for Aegis digital twin platform."""

from __future__ import annotations

import logging
import webbrowser
from pathlib import Path

import uvicorn

from services.backend.db import init_db, seed_database_if_empty

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("aegis.demo")


def main() -> None:
    logger.info("=" * 70)
    logger.info("   AEGIS: TYPE 2 DIABETES DIGITAL TWIN RESEARCH PROTOTYPE")
    logger.info("   Postprandial 180-min Trajectory Forecast & Replay Platform")
    logger.info("=" * 70)

    # 1. Check bundle artifacts
    bundle_dir = Path("artifacts/bundle")
    if not bundle_dir.exists() or not (bundle_dir / "model.pt").exists():
        logger.warning(
            "Artifact bundle not found in artifacts/bundle/. Model will run in fallback mock mode."
        )
    else:
        logger.info(f"Verified Candidate S model artifact bundle at {bundle_dir.resolve()}")

    # 2. Initialize and seed DB
    logger.info("Initializing relational database and seeding demo patient twins...")
    init_db()
    seed_database_if_empty()

    import argparse
    import os

    parser = argparse.ArgumentParser(description="Aegis Digital Twin Offline Clinician Demo")
    parser.add_argument(
        "--port",
        "-p",
        type=int,
        default=int(os.environ.get("AEGIS_PORT", os.environ.get("PORT", "8080"))),
        help="Port to bind the demo server to (default: 8080 or AEGIS_PORT)",
    )
    parser.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",
        help="Host address to bind to (default: 0.0.0.0)",
    )
    parser.add_argument(
        "--no-browser",
        action="store_true",
        help="Do not auto-open the browser dashboard",
    )
    args, _ = parser.parse_known_args()

    port = args.port
    host = args.host

    # 3. Open browser dashboard
    dash_url = f"http://localhost:{port}/dashboard"
    logger.info(f"Starting server on http://{host}:{port} (Clinician Dashboard: {dash_url})")

    if not args.no_browser:
        try:
            webbrowser.open(dash_url)
        except Exception:
            pass

    # 4. Start uvicorn
    uvicorn.run("services.backend.main:app", host=host, port=port, reload=False)


if __name__ == "__main__":
    main()
