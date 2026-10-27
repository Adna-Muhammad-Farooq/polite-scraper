
from pathlib import Path
import time

import requests


BASE_DIR = Path(__file__).resolve().parent.parent
CACHE_DIR = BASE_DIR / "cache"
CACHE_FILE = CACHE_DIR / "catalogue-page-1.html"

CATALOGUE_URL = "https://books.toscrape.com/"

HEADERS = {
    "User-Agent": (
        "FlyRankInternship-A9/1.0 "
        "(educational scraper; "
        "https://github.com/Adna-Muhammad-Farooq/polite-scraper)"
    )
}

TIMEOUT_SECONDS = 10
REQUEST_DELAY_SECONDS = 0.5


def fetch_catalogue():
    """Fetch the first catalogue page once and reuse its cached HTML."""

    if CACHE_FILE.exists():
        html = CACHE_FILE.read_text(encoding="utf-8")
        print(f"CACHE HIT | bytes={CACHE_FILE.stat().st_size}")
        return html

    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    # Be polite before making a real network request.
    time.sleep(REQUEST_DELAY_SECONDS)

    try:
        response = requests.get(
            CATALOGUE_URL,
            headers=HEADERS,
            timeout=TIMEOUT_SECONDS,
        )

        # Check HTTP status before treating the response as HTML.
        print(f"HTTP status: {response.status_code}")
        response.raise_for_status()

        if response.status_code != 200:
            raise requests.HTTPError(
                f"Expected HTTP 200, received {response.status_code}"
            )

        html = response.text
        CACHE_FILE.write_text(html, encoding="utf-8")

        print(f"FETCH | status=200 | bytes={len(response.content)}")
        print(f"Saved HTML to: {CACHE_FILE.relative_to(BASE_DIR)}")

        return html

    except requests.RequestException as error:
        print(f"FETCH FAILED | {type(error).__name__}: {error}")
        return None


def main():
    html = fetch_catalogue()

    if html is None:
        print("Stage 1 failed: no catalogue HTML available.")
        return

    print("Stage 1 checkpoint: catalogue HTML is available.")
    print(f"HTML characters: {len(html)}")


if __name__ == "__main__":
    main()
