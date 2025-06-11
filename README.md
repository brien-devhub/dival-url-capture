# DivaDance URL Capture Tool

This script reads a CSV containing DivaDance location `site_id` and `mb_site_id`, builds a temporary HTML page with the Mindbody login widget, and captures the resulting Mindbody session URL (`/session/new`) using Playwright.

## Features

- Captures only valid Mindbody session URLs
- Skips existing and invalid rows
- Logs all actions to `logs/`
- Saves failures to `failures.csv`
- Processes up to 500 rows per run

## Requirements

- Python 3.9+
- Google Chrome/Chromium
- Playwright Python

## Setup

```bash
pip install -r requirements.txt
playwright install
