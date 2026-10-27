# Polite Scraper

A Python web scraper built for the FlyRank Backend AI Engineering assignment. It collects book information from [Books to Scrape](https://books.toscrape.com/), a website designed for scraping practice.

## Project Scope

The scraper inspects the first three catalogue pages and discovers unique book detail URLs.

It collects the following fields:

- Book title
- Product URL
- Original price text
- Normalized price in GBP
- Availability
- Star rating
- Book description
- Source catalogue page
- Fetch timestamp

## Technologies

- Python
- Requests
- Beautiful Soup
- JSON Schema validation

## Features

- Fetches catalogue and book detail pages.
- Caches downloaded HTML to reduce repeated network requests.
- Uses a descriptive User-Agent and request timeout.
- Waits between network requests.
- Retries temporary request failures up to three times.
- Extracts and normalizes book prices.
- Validates records against `schema.json`.
- Handles fetch, extraction, and validation errors.
- Saves records, errors, and a run summary as JSON.

## Project Structure

```text
polite-scraper/
├── src/
│   └── main.py
├── schema.json
├── requirements.txt
├── .gitignore
└── README.md
```

The `cache/` and `output/` directories are generated locally. They should remain excluded from Git.

## Setup

Create and activate a virtual environment on Windows:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
pip install -r requirements.txt
```

Run the scraper from the project root:

```powershell
python src/main.py
```

## Output Files

The scraper generates these files in the `output/` directory:

- `books.json`: successfully extracted and validated book records.
- `errors.json`: recorded fetch, extraction, and validation errors.
- `run-report.json`: summary of the latest run.

Downloaded HTML is stored in `