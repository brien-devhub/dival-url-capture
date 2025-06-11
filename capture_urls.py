import pandas as pd
import asyncio
import tempfile
from pathlib import Path
from datetime import datetime
from playwright.async_api import async_playwright

INPUT_CSV = "DivaDance Existing Client Login links - Sheet1 (1).csv"
OUTPUT_CSV = "updated_output.csv"
MATCH_STRING = "cart.mindbodyonline.com/sites"
LOG_DIR = "logs"
MAX_ROWS = 500
WAIT_MS = 10000

# Ensure logs folder exists
Path(LOG_DIR).mkdir(parents=True, exist_ok=True)
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
log_file_path = Path(LOG_DIR) / f"run_{timestamp}.log"

def log(msg):
    print(msg)
    with open(log_file_path, "a") as f:
        f.write(msg + "\n")

def build_html(site_id, mb_site_id):
    return f"""<!DOCTYPE html>
<html>
<head>
  <script src="https://widgets.mindbodyonline.com/javascripts/healcode.js" type="text/javascript"></script>
</head>
<body>
  <healcode-widget 
    data-version="0.2" 
    data-link-class="loginRegister" 
    data-site-id="{site_id}" 
    data-mb-site-id="{mb_site_id}" 
    data-bw-identity-site="true" 
    data-type="account-link" 
    data-inner-html="Login">
  </healcode-widget>
</body>
</html>
"""

async def capture_url(context, html_content):
    captured = {"url": ""}

    page = await context.new_page()

    async def handler(request):
        if MATCH_STRING in request.url:
            log(f"  Matched: {request.url}")
            captured["url"] = request.url

    page.on("request", handler)

    with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as tmp_file:
        tmp_file.write(html_content.encode("utf-8"))
        tmp_path = Path(tmp_file.name).resolve().as_uri()

    try:
        await page.goto(tmp_path, timeout=15000)
        await page.wait_for_timeout(WAIT_MS)
    except Exception as e:
        log(f"  Navigation error: {e}")
    finally:
        await page.close()

    return captured["url"]

async def process_csv():
    df = pd.read_csv(INPUT_CSV)
    processed = 0

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()

        for idx, row in df.iterrows():
            if processed >= MAX_ROWS:
                log(f"\nRow limit of {MAX_ROWS} reached. Stopping.")
                break

            site_id = str(row.get("site_id", "")).strip()
            mb_site_id = str(row.get("mb_site_id", "")).strip()
            existing_url = str(row.get("URL", "")).strip()

            if not site_id or not mb_site_id or site_id.lower() == "nan" or mb_site_id.lower() == "nan":
                log(f"[{idx + 1}] Invalid or missing IDs. Skipping.")
                continue

            if existing_url:
                log(f"[{idx + 1}] URL already exists. Skipping.")
                continue

            log(f"\n[{idx + 1}] Capturing URL for site_id={site_id}, mb_site_id={mb_site_id}")
            html = build_html(site_id, mb_site_id)

            try:
                captured_url = await capture_url(context, html)
                df.at[idx, 'URL'] = captured_url or ""
                processed += 1
            except Exception as e:
                df.at[idx, 'URL'] = "ERROR"
                log(f"  Capture error: {e}")

        await browser.close()

    df.to_csv(OUTPUT_CSV, index=False)
    log(f"\nFinished. Processed {processed} rows. Output saved to: {OUTPUT_CSV}")

if __name__ == "__main__":
    asyncio.run(process_csv())
import pandas as pd
import asyncio
import tempfile
from pathlib import Path
from datetime import datetime
from playwright.async_api import async_playwright

INPUT_CSV = "DivaDance Existing Client Login links - Sheet1 (1).csv"
OUTPUT_CSV = "updated_output.csv"
MATCH_STRING = "cart.mindbodyonline.com/sites"
LOG_DIR = "logs"
MAX_ROWS = 500
WAIT_MS = 10000  # 10 seconds

# Ensure logs folder exists
Path(LOG_DIR).mkdir(parents=True, exist_ok=True)
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
log_file_path = Path(LOG_DIR) / f"run_{timestamp}.log"

def log(msg):
    print(msg)
    with open(log_file_path, "a") as f:
        f.write(msg + "\n")

def build_html(site_id, mb_site_id):
    return f"""<!DOCTYPE html>
<html>
<head>
  <script src="https://widgets.mindbodyonline.com/javascripts/healcode.js" type="text/javascript"></script>
</head>
<body>
  <healcode-widget 
    data-version="0.2" 
    data-link-class="loginRegister" 
    data-site-id="{site_id}" 
    data-mb-site-id="{mb_site_id}" 
    data-bw-identity-site="true" 
    data-type="account-link" 
    data-inner-html="Login">
  </healcode-widget>
</body>
</html>
"""

async def capture_url(page, html_content, match_string):
    captured = {"url": ""}

    async def handler(request):
        if match_string in request.url:
            log(f"  ↪ Matched: {request.url}")
            captured["url"] = request.url

    page.on("request", handler)

    with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as tmp_file:
        tmp_file.write(html_content.encode("utf-8"))
        tmp_path = Path(tmp_file.name).resolve().as_uri()

    try:
        await page.goto(tmp_path, timeout=15000)
        await page.wait_for_timeout(WAIT_MS)
    except Exception as e:
        log(f"  ⚠️ Navigation error: {e}")

    page.off("request", handler)
    return captured["url"]

async def process_csv():
    df = pd.read_csv(INPUT_CSV)
    processed = 0

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        for idx, row in df.iterrows():
            if processed >= MAX_ROWS:
                log(f"\n🚫 Max row limit {MAX_ROWS} reached. Stopping.")
                break

            site_id = str(row.get("site_id", "")).strip()
            mb_site_id = str(row.get("mb_site_id", "")).strip()
            existing_url = str(row.get("URL", "")).strip()

            if not site_id or not mb_site_id or site_id.lower() == "nan" or mb_site_id.lower() == "nan":
                log(f"[{idx + 1}] ❌ Missing or invalid site IDs. Skipping.")
                continue

            if existing_url:
                log(f"[{idx + 1}] ✅ URL already exists. Skipping.")
                continue

            log(f"\n[{idx + 1}] ▶️ Capturing for site_id={site_id}, mb_site_id={mb_site_id}")
            html = build_html(site_id, mb_site_id)
            try:
                captured_url = await capture_url(page, html, MATCH_STRING)
                df.at[idx, 'URL'] = captured_url or ""
                processed += 1
            except Exception as e:
                df.at[idx, 'URL'] = "ERROR"
                log(f"  ❌ Capture error: {e}")

        await browser.close()

    df.to_csv(OUTPUT_CSV, index=False)
    log(f"\n✅ Finished. Processed {processed} rows. Output saved to: {OUTPUT_CSV}")

if __name__ == "__main__":
    asyncio.run(process_csv())
import pandas as pd
import asyncio
import tempfile
from pathlib import Path
from datetime import datetime
from playwright.async_api import async_playwright

INPUT_CSV = "DivaDance Existing Client Login links - Sheet1 (1).csv"
OUTPUT_CSV = "updated_output.csv"
MATCH_STRING = "cart.mindbodyonline.com/sites"
LOG_DIR = "logs"
MAX_ROWS = 500

# Ensure logs folder exists
Path(LOG_DIR).mkdir(parents=True, exist_ok=True)

# Create log file
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
log_file_path = Path(LOG_DIR) / f"run_{timestamp}.log"

def log(msg):
    print(msg)
    with open(log_file_path, "a") as log_file:
        log_file.write(msg + "\n")

def build_html(site_id, mb_site_id):
    return f"""<!DOCTYPE html>
<html>
<head>
  <script src="https://widgets.mindbodyonline.com/javascripts/healcode.js" type="text/javascript"></script>
</head>
<body>
  <healcode-widget 
    data-version="0.2" 
    data-link-class="loginRegister" 
    data-site-id="{site_id}" 
    data-mb-site-id="{mb_site_id}" 
    data-bw-identity-site="true" 
    data-type="account-link" 
    data-inner-html="Login">
  </healcode-widget>
</body>
</html>
"""

async def capture_url_from_html(html_content, match_string):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        captured_url = ""

        async def handle_request(request):
            nonlocal captured_url
            if match_string in request.url:
                captured_url = request.url

        page.on("request", handle_request)

        with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as tmp_file:
            tmp_file.write(html_content.encode("utf-8"))
            tmp_path = Path(tmp_file.name).resolve().as_uri()

        try:
            await page.goto(tmp_path, timeout=15000)
            await page.wait_for_timeout(5000)
        except Exception as e:
            log(f"Navigation error: {e}")

        await browser.close()
        return captured_url

async def process_csv():
    df = pd.read_csv(INPUT_CSV)
    processed = 0

    for idx, row in df.iterrows():
        if processed >= MAX_ROWS:
            log(f"\n🚫 Reached row limit of {MAX_ROWS}. Stopping.")
            break

        url = str(row.get('URL', '')).strip()
        site_id = str(row.get('site_id', '')).strip()
        mb_site_id = str(row.get('mb_site_id', '')).strip()

        if not site_id or not mb_site_id:
            log(f"[{idx + 1}] Missing IDs, skipping.")
            continue

        if url:
            log(f"[{idx + 1}] URL already populated, skipping.")
            continue

        log(f"\n[{idx + 1}] Capturing: site_id={site_id}, mb_site_id={mb_site_id}")
        html = build_html(site_id, mb_site_id)

        try:
            captured_url = await capture_url_from_html(html, MATCH_STRING)
            log(f"Captured URL: {captured_url}")
            df.at[idx, 'URL'] = captured_url or ""
        except Exception as e:
            log(f"Error processing row {idx + 1}: {e}")
            df.at[idx, 'URL'] = "ERROR"

        processed += 1

    df.to_csv(OUTPUT_CSV, index=False)
    log(f"\n✅ Done. Processed {processed} rows. Saved to: {OUTPUT_CSV}")

if __name__ == "__main__":
    asyncio.run(process_csv())

import pandas as pd
import asyncio
import tempfile
from pathlib import Path
from playwright.async_api import async_playwright

INPUT_CSV = "DivaDance Existing Client Login links - Sheet1 (1).csv"
OUTPUT_CSV = "updated_output.csv"
MATCH_STRING = "cart.mindbodyonline.com/sites"

def build_html(site_id, mb_site_id):
    return f"""<!DOCTYPE html>
<html>
<head>
  <script src="https://widgets.mindbodyonline.com/javascripts/healcode.js" type="text/javascript"></script>
</head>
<body>
  <healcode-widget 
    data-version="0.2" 
    data-link-class="loginRegister" 
    data-site-id="{site_id}" 
    data-mb-site-id="{mb_site_id}" 
    data-bw-identity-site="true" 
    data-type="account-link" 
    data-inner-html="Login">
  </healcode-widget>
</body>
</html>
"""

async def capture_url_from_html(html_content, match_string):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        captured_url = ""

        async def handle_request(request):
            nonlocal captured_url
            if match_string in request.url:
                captured_url = request.url

        page.on("request", handle_request)

        with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as tmp_file:
            tmp_file.write(html_content.encode("utf-8"))
            tmp_path = Path(tmp_file.name).resolve().as_uri()

        try:
            await page.goto(tmp_path, timeout=15000)
            await page.wait_for_timeout(5000)
        except Exception as e:
            print(f"Error: {e}")

        await browser.close()
        return captured_url

async def process_csv():
    df = pd.read_csv(INPUT_CSV)

    for idx, row in df.iterrows():
        site_id = str(row['site_id']).strip()
        mb_site_id = str(row['mb_site_id']).strip()

        if not site_id or not mb_site_id:
            print(f"[{idx + 1}] Missing site ID(s), skipping.")
            continue

        print(f"\n[{idx + 1}] Processing: site_id={site_id}, mb_site_id={mb_site_id}")
        html = build_html(site_id, mb_site_id)
        try:
            captured_url = await capture_url_from_html(html, MATCH_STRING)
            print(f"Captured URL: {captured_url}")
            df.at[idx, 'URL'] = captured_url or ""
        except Exception as e:
            print(f"Failed row {idx + 1}: {e}")
            df.at[idx, 'URL'] = "ERROR"

    df.to_csv(OUTPUT_CSV, index=False)
    print(f"\n✅ Saved output to {OUTPUT_CSV}")

if __name__ == "__main__":
    asyncio.run(process_csv())
import pandas as pd
import asyncio
import tempfile
from pathlib import Path
from playwright.async_api import async_playwright

INPUT_CSV = "DivaDance Existing Client Login links - Sheet1 (1).csv"
OUTPUT_CSV = "updated_output.csv"
MATCH_STRING = "mindbodyonline"  # Change if you want a more precise match

# Template for a temporary HTML file
def build_html(site_id, mb_site_id):
    return f"""<!DOCTYPE html>
<html>
<head>
  <script src="https://widgets.mindbodyonline.com/javascripts/healcode.js" type="text/javascript"></script>
</head>
<body>
  <healcode-widget 
    data-version="0.2" 
    data-link-class="loginRegister" 
    data-site-id="{site_id}" 
    data-mb-site-id="{mb_site_id}" 
    data-bw-identity-site="true" 
    data-type="account-link" 
    data-inner-html="Login">
  </healcode-widget>
</body>
</html>
"""

async def capture_url_from_html(html_content, match_string):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        captured_url = ""

        async def handle_request(request):
            nonlocal captured_url
            if match_string in request.url:
                captured_url = request.url

        page.on("request", handle_request)

        with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as tmp_file:
            tmp_file.write(html_content.encode("utf-8"))
            tmp_path = Path(tmp_file.name).resolve().as_uri()

        try:
            await page.goto(tmp_path, timeout=15000)
            await page.wait_for_timeout(5000)
        except Exception as e:
            print(f"Error: {e}")

        await browser.close()
        return captured_url

async def process_csv():
    df = pd.read_csv(INPUT_CSV)

    for idx, row in df.iterrows():
        site_id = str(row['site_id'])
        mb_site_id = str(row['mb_site_id'])

        print(f"\n[{idx + 1}] Processing: site_id={site_id}, mb_site_id={mb_site_id}")
        html = build_html(site_id, mb_site_id)
        try:
            captured_url = await capture_url_from_html(html, MATCH_STRING)
            print(f"Captured URL: {captured_url}")
            df.at[idx, 'URL'] = captured_url or ""
        except Exception as e:
            print(f"Failed row {idx + 1}: {e}")
            df.at[idx, 'URL'] = "ERROR"

    df.to_csv(OUTPUT_CSV, index=False)
    print(f"\n✅ Saved output to {OUTPUT_CSV}")

if __name__ == "__main__":
    asyncio.run(process_csv())
import pandas as pd
import asyncio
from playwright.async_api import async_playwright

INPUT_CSV = "DivaDance Existing Client Login links - Sheet1 (1).csv"
OUTPUT_CSV = "updated_output.csv"

# Match part of the URL from the network request
MATCH_PATTERN = "mindbodyonline"

async def capture_request_url(script_url, match_string):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        captured_url = ""

        async def handle_request(request):
            nonlocal captured_url
            if match_string in request.url:
                captured_url = request.url

        page.on("request", handle_request)

        try:
            await page.goto(script_url, timeout=15000)
            await page.wait_for_timeout(5000)
        except Exception as e:
            print(f"Error navigating to {script_url}: {e}")

        await browser.close()
        return captured_url

async def process_csv():
    df = pd.read_csv(INPUT_CSV)

    # Read the script URL from H2 (first row, 7th index since CSV is 0-indexed)
    script_url = df.iloc[0, 7]
    print(f"Script URL to run: {script_url}")

    for idx, row in df.iterrows():
        print(f"\nProcessing row {idx + 1}:")
        try:
            captured_url = await capture_request_url(script_url, MATCH_PATTERN)
            print(f"Captured URL: {captured_url}")
            df.at[idx, 'URL'] = captured_url or ""
        except Exception as e:
            print(f"Row {idx + 1} failed: {e}")
            df.at[idx, 'URL'] = "ERROR"

    df.to_csv(OUTPUT_CSV, index=False)
    print(f"\n✅ Updated file saved as: {OUTPUT_CSV}")

if __name__ == "__main__":
    asyncio.run(process_csv())
import pandas as pd
import asyncio
from playwright.async_api import async_playwright

INPUT_CSV = "DivaDance Existing Client Login links - Sheet1 (1).csv"
OUTPUT_CSV = "updated_output.csv"

def build_url(site_id, mb_site_id):
    return f"https://locations.divadancecompany.com/client-login?site_id={site_id}&mb_site_id={mb_site_id}"

async def capture_request_url(target_url, match_string):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        captured_url = ""

        async def handle_request(request):
            nonlocal captured_url
            if match_string in request.url:
                captured_url = request.url

        page.on("request", handle_request)
        try:
            await page.goto(target_url, timeout=15000)
            await page.wait_for_timeout(5000)
        except:
            pass

        await browser.close()
        return captured_url

async def process_csv():
    df = pd.read_csv(INPUT_CSV)

    for idx, row in df.iterrows():
        site_id = row['site ID']
        mb_site_id = row['mb site ID']
        target_url = build_url(site_id, mb_site_id)

        print(f"[{idx}] Navigating to {target_url}")
        captured_url = await capture_request_url(target_url, match_string="mindbodyonline")

        print(f"Captured URL: {captured_url}")
        df.at[idx, 'url'] = captured_url or ""

    df.to_csv(OUTPUT_CSV, index=False)
    print(f"\nUpdated file saved as: {OUTPUT_CSV}")

if __name__ == "__main__":
    asyncio.run(process_csv())

