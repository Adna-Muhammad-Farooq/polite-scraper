
from pathlib import Path
from urllib.parse import urljoin
from datetime import datetime, timezone
import json
import re
import time

import requests
from bs4 import BeautifulSoup
from jsonschema import Draft202012Validator


# --------------------------------------------------
# Configuration
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent
CACHE_DIR = BASE_DIR / "cache"
OUTPUT_DIR = BASE_DIR / "output"

BASE_URL = "https://books.toscrape.com/"
CATALOGUE_URL = BASE_URL
SCHEMA_FILE = BASE_DIR / "schema.json"

BOOKS_OUTPUT = OUTPUT_DIR / "books.json"
ERRORS_OUTPUT = OUTPUT_DIR / "errors.json"
REPORT_OUTPUT = OUTPUT_DIR / "run-report.json"

HEADERS = {
    "User-Agent": (
        "FlyRankInternship-A9/1.0 "
        "(educational scraper)"
    )
}

TIMEOUT_SECONDS = 10
REQUEST_DELAY_SECONDS = 0.5


# --------------------------------------------------
# Fetch pages and reuse cached HTML
# --------------------------------------------------

def fetch_page(url):
    """Fetch a page and reuse cached HTML when available."""

    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    if url == CATALOGUE_URL:
        cache_name = "catalogue-page-1.html"

    elif "/catalogue/page-" in url:
        page_number = url.split("page-")[-1].replace(".html", "")
        cache_name = f"catalogue-page-{page_number}.html"

    else:
        # Book URLs end with /index.html.
        # Use the book's unique folder name for the cache file.
        path_parts = url.rstrip("/").split("/")

        if path_parts[-1] == "index.html" and len(path_parts) >= 2:
            book_slug = path_parts[-2]
        else:
            book_slug = path_parts[-1].replace(".html", "")

        cache_name = f"book-{book_slug}.html"

    cache_file = CACHE_DIR / cache_name

    if cache_file.exists():
        print(f"CACHE HIT | {cache_name}")
        return cache_file.read_text(encoding="utf-8")

    # Wait before making a real network request.
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


# --------------------------------------------------
# Discover catalogue pages
# --------------------------------------------------

def discover_catalogue_pages():
    """Return the first three catalogue page URLs."""

    return [
        CATALOGUE_URL,
        urljoin(CATALOGUE_URL, "catalogue/page-2.html"),
        urljoin(CATALOGUE_URL, "catalogue/page-3.html"),
    ]


def discover_book_urls(html, page_url):
    """Extract unique book detail URLs from a catalogue page."""

    soup = BeautifulSoup(html, "html.parser")
    book_urls = []

    for link in soup.select("article.product_pod h3 a"):
        href = link.get("href")

        if not href:
            continue

        book_url = urljoin(page_url, href)

        if book_url not in book_urls:
            book_urls.append(book_url)

    return book_urls


# --------------------------------------------------
# Extract book details
# --------------------------------------------------

def extract_book_details(html, product_url, source_page):
    """Extract book details and normalize the price."""

    soup = BeautifulSoup(html, "html.parser")

    title_element = soup.select_one("div.product_main h1")
    price_element = soup.select_one(
        "div.product_main .price_color"
    )
    availability_element = soup.select_one(
        "div.product_main .availability"
    )
    rating_element = soup.select_one(
        "div.product_main p.star-rating"
    )

    if title_element is None:
        raise ValueError("Book title was not found")

    if price_element is None:
        raise ValueError("Book price was not found")

    if availability_element is None:
        raise ValueError("Book availability was not found")

    if rating_element is None:
        raise ValueError("Book rating was not found")

    title = title_element.get_text(" ", strip=True)
    price_text = price_element.get_text(" ", strip=True)
    availability_text = availability_element.get_text(
        " ", strip=True
    )

    # The rating is stored in the element's CSS class.
    rating_classes = rating_element.get("class", [])

    rating_text = next(
        (
            item
            for item in rating_classes
            if item in {"One", "Two", "Three", "Four", "Five"}
        ),
        "Unknown",
    )

    description_element = soup.select_one(
        "#product_description + p"
    )

    description = (
        description_element.get_text(" ", strip=True)
        if description_element
        else None
    )

    # Convert a price such as £51.77 into 51.77.
    price_match = re.search(
        r"\d+(?:\.\d{1,2})?",
        price_text,
    )

    if not price_match:
        raise ValueError(f"Could not parse price: {price_text}")

    price_gbp = float(price_match.group())

    return {
        "title": title,
        "product_url": product_url,
        "price_text": price_text,
        "price_gbp": price_gbp,
        "availability_text": availability_text,
        "rating_text": rating_text,
        "description": description,
        "source_page": source_page,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
    }


# --------------------------------------------------
# Validate records against schema.json
# --------------------------------------------------

def validate_record(record, validator):
    """Return validation errors, or None if the record is valid."""

    validation_errors = sorted(
        validator.iter_errors(record),
        key=lambda error: list(error.path),
    )

    if not validation_errors:
        return None

    return "; ".join(
        error.message for error in validation_errors
    )


# --------------------------------------------------
# Save JSON output
# --------------------------------------------------

def save_json(path, data):
    """Save data as readable JSON."""

    path.parent.mkdir(parents=True, exist_ok=True)

    path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


# --------------------------------------------------
# Main scraper
# --------------------------------------------------

def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    if not SCHEMA_FILE.exists():
        raise FileNotFoundError(
            f"Schema file not found: {SCHEMA_FILE}"
        )

    schema = json.loads(
        SCHEMA_FILE.read_text(encoding="utf-8")
    )

    validator = Draft202012Validator(schema)

    catalogue_pages = discover_catalogue_pages()

    all_book_urls = []
    book_source_pages = {}
    books = []
    errors = []

    catalogue_failures = 0
    book_fetch_failures = 0
    validation_failures = 0
    extraction_failures = 0

    print(
        f"Catalogue pages to inspect: {len(catalogue_pages)}"
    )

    # Stage 2: Discover books and remember their source pages.
    for page_url in catalogue_pages:
        html = fetch_page(page_url)

        if html is None:
            catalogue_failures += 1

            errors.append({
                "url": page_url,
                "stage": "catalogue_fetch",
                "error": "Could not fetch catalogue page",
            })

            continue

        page_book_urls = discover_book_urls(html, page_url)

        print(
            f"Books discovered on this page: "
            f"{len(page_book_urls)}"
        )

        for book_url in page_book_urls:
            if book_url not in book_source_pages:
                all_book_urls.append(book_url)
                book_source_pages[book_url] = page_url

    print("\nStage 2 discovery summary")
    print(f"Catalogue pages requested: {len(catalogue_pages)}")
    print(f"Unique book URLs discovered: {len(all_book_urls)}")

    # Stage 3: Fetch book pages and extract their details.
    for index, product_url in enumerate(all_book_urls, start=1):
        print(
            f"\nProcessing book {index}/{len(all_book_urls)}"
        )

        source_page = book_source_pages.get(
            product_url,
            CATALOGUE_URL,
        )

        html = fetch_page(product_url)

        if html is None:
            book_fetch_failures += 1

            errors.append({
                "url": product_url,
                "stage": "book_fetch",
                "error": "Could not fetch book detail page",
            })

            continue

        try:
            record = extract_book_details(
                html,
                product_url,
                source_page,
            )

        except (ValueError, AttributeError, TypeError) as error:
            extraction_failures += 1

            errors.append({
                "url": product_url,
                "stage": "extraction",
                "error": str(error),
            })

            continue

        validation_error = validate_record(record, validator)

        if validation_error:
            validation_failures += 1

            errors.append({
                "url": product_url,
                "stage": "validation",
                "error": validation_error,
                "record": record,
            })

            continue

        books.append(record)

    # Save the valid records and errors.
    save_json(BOOKS_OUTPUT, books)
    save_json(ERRORS_OUTPUT, errors)

    # Create a summary of the run.
    report = {
        "catalogue_pages_requested": len(catalogue_pages),
        "catalogue_fetch_failures": catalogue_failures,
        "unique_book_urls_discovered": len(all_book_urls),
        "book_fetch_failures": book_fetch_failures,
        "extraction_failures": extraction_failures,
        "validation_failures": validation_failures,
        "valid_records": len(books),
        "total_errors": len(errors),
        "completed_at": datetime.now(timezone.utc).isoformat(),
    }

    save_json(REPORT_OUTPUT, report)

    print("\nScraper run summary")
    print(json.dumps(report, indent=2))

    print(f"\nBooks saved to: {BOOKS_OUTPUT}")
    print(f"Errors saved to: {ERRORS_OUTPUT}")
    print(f"Report saved to: {REPORT_OUTPUT}")


if __name__ == "__main__":
    main()
