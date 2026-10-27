# Polite Scraper

A Python web scraper for the FlyRank Backend AI Engineering Week 5 assignment.

## Stage 0: Target Classification

- **Target:** [Books to Scrape](https://books.toscrape.com/)
- **Purpose:** Practice collecting book information from a website designed for scraping exercises.
- **Scope:** The first three catalogue pages and the 60 unique book detail pages linked from them.
- **Data collected:** Book title, product URL, price, availability, rating, description, source page, and fetch timestamp.
- **robots.txt check:** Opened https://books.toscrape.com/robots.txt. The browser showed a blank page; no directives were visible. This result has not been treated as permission by itself.
- **Politeness:** The scraper will identify itself with a User-Agent, use a timeout, wait at least 500 ms between real requests, check HTTP status codes, and reuse cached HTML during development.

### Responsible Scraping

I will not reuse this code on another site without checking its rules and terms first.

## Planned Output

- `cache/`: Saved HTML pages.
- `output/books.json`: Clean, validated book records.
- `output/errors.json`: Records that fail validation.
- `output/run-report.json`: Summary of the scraper run.

## Status

Stage 0 documentation started. Later stages will be recorded as they are implemented and tested.