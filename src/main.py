
from pathlib import Path
import time

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin


BASE_DIR = Path(__file__).resolve().parent.parent
CACHE_DIR = BASE_DIR / "cache"

BASE_URL = "https://books.toscrape.com/"
CATALOGUE_URL = BASE_URL

HEADERS = {
    "User-Agent": (
        "FlyRankInternship-A9/1.0 "
        "(educational scraper)"
    )
}

TIMEOUT_SECONDS = 10
REQUEST_DELAY_SECONDS = 0.5


def fetch_page(url):
    """Fetch a page, using its cached HTML when available."""

    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    # Create a predictable cache filename for each URL.
    if url == CATALOGUE_URL:
        cache_name = "catalogue-page-1.html"
    else:
        page_number = url.split("page-")[-1].replace(".html", "")
        cache_name = f"catalogue-page-{page_number}.html"

    cache_file = CACHE_DIR / cache_name

    if cache_file.exists():
        print(f"CACHE HIT | {cache_name}")
        return cache_file.read_text(encoding="utf-8")

    time.sleep(REQUEST_DELAY_SECONDS)

    try:
        response = requests.get(
            url,
            headers=HEADERS,
            timeout=TIMEOUT_SECONDS,
        )
        response.raise_for_status()

        if response.status_code != 200:
            raise requests.HTTPError(
                f"Expected HTTP 200, received {response.status_code}"
            )

        cache_file.write_text(response.text, encoding="utf-8")
        print(f"FETCH | status={response.status_code} | {url}")

        return response.text

    except requests.RequestException as error:
        print(f"FETCH FAILED | {url} | {error}")
        return None


def discover_catalogue_pages():
    """Return the first three catalogue page URLs."""

    pages = [
        CATALOGUE_URL,
        urljoin(CATALOGUE_URL, "catalogue/page-2.html"),
        urljoin(CATALOGUE_URL, "catalogue/page-3.html"),
    ]

    return pages


def discover_book_urls(html, page_url):
    """Extract unique book detail URLs from one catalogue page."""

    soup = BeautifulSoup(html, "html.parser")
    book_urls = []

    for link in soup.select("article.product_pod h3 a"):
        book_url = urljoin(page_url, link.get("href", ""))

        if book_url not in book_urls:
            book_urls.append(book_url)

    return book_urls


def main():
    catalogue_pages = discover_catalogue_pages()
    all_book_urls = []

    print(f"Catalogue pages to inspect: {len(catalogue_pages)}")

    for page_url in catalogue_pages:
        html = fetch_page(page_url)

        if html is None:
            print(f"Skipping unavailable catalogue page: {page_url}")
            continue

        page_book_urls = discover_book_urls(html, page_url)
        print(f"Books discovered on this page: {len(page_book_urls)}")

        for book_url in page_book_urls:
            if book_url not in all_book_urls:
                all_book_urls.append(book_url)

    print("\nStage 2 discovery summary")
    print(f"Catalogue pages requested: {len(catalogue_pages)}")
    print(f"Unique book URLs discovered: {len(all_book_urls)}")

    for book_url in all_book_urls[:5]:
        print(f"- {book_url}")


if __name__ == "__main__":
    main()
