import json
import logging
import os
import re
import time
import pandas as pd
import requests
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

IMDB_URL = "https://www.imdb.com/chart/top/"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Sec-Ch-Ua": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"Windows"',
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",
}

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FALLBACK_CSV_PATH = os.path.join(BASE_DIR, "downloads", "imdb_top_250_movies.csv")


def clean_year(value):
    """Convert IMDb release-year data to an integer."""
    if isinstance(value, dict):
        value = value.get("year")

    if isinstance(value, int):
        return value

    if value is not None:
        match = re.search(r"\b(19\d{2}|20\d{2})\b", str(value))
        if match:
            return int(match.group(1))

    return 0


def clean_rating(value):
    """Convert a rating value to a float."""
    if isinstance(value, dict):
        value = value.get("aggregateRating") or value.get("ratingValue")

    try:
        return round(float(value), 1) if value is not None else 0.0
    except (TypeError, ValueError):
        return 0.0


def parse_movie_item(item, fallback_rank):
    """Extract a movie from an HTML list item."""
    title_element = item.select_one(
        "h3.ipc-title__text, h3, h4, a.ipc-title-link-wrapper"
    )

    if not title_element:
        return None

    header = title_element.get_text(" ", strip=True)

    rank_match = re.match(r"^\s*(\d+)\.\s*(.+)$", header)
    if rank_match:
        rank = int(rank_match.group(1))
        title = rank_match.group(2).strip()
    else:
        rank = fallback_rank
        title = header

    metadata = item.select_one(".cli-title-metadata")
    year = 0

    if metadata:
        for element in metadata.select("li, span"):
            year_match = re.search(
                r"\b(19\d{2}|20\d{2})\b",
                element.get_text(" ", strip=True),
            )
            if year_match:
                year = int(year_match.group(1))
                break

    if not year:
        year_match = re.search(
            r"\b(19\d{2}|20\d{2})\b",
            item.get_text(" ", strip=True),
        )
        if year_match:
            year = int(year_match.group(1))

    rating = 0.0
    rating_element = item.select_one(".ipc-rating-star")

    if rating_element:
        rating_match = re.search(
            r"(?<!\d)(10(?:\.0)?|[0-9]\.[0-9])(?!\d)",
            rating_element.get_text(" ", strip=True),
        )
        if rating_match:
            rating = float(rating_match.group(1))

    if not rating:
        rating_match = re.search(r"\b(\d\.\d)\b", item.get_text(" ", strip=True))
        if rating_match:
            rating = float(rating_match.group(1))

    return {
        "Rank": rank,
        "Movie Title": title,
        "Release Year": year,
        "IMDb Rating": rating,
    }


def extract_json_movies(soup):
    """Extract movie data from embedded JSON (JSON-LD or __NEXT_DATA__)."""
    results = []

    def walk(node):
        if isinstance(node, dict):
            # IMDb JSON-LD itemListElement format
            if node.get("@type") == "Movie" or "aggregateRating" in node or "titleText" in node:
                title_data = node.get("titleText")
                title = (
                    title_data.get("text")
                    if isinstance(title_data, dict)
                    else node.get("name")
                )

                rating_data = node.get("ratingsSummary") or node.get("aggregateRating") or {}
                if isinstance(rating_data, dict):
                    rating = rating_data.get("aggregateRating") or rating_data.get("ratingValue") or 0.0
                else:
                    rating = rating_data

                year = clean_year(
                    node.get("releaseYear")
                    or node.get("datePublished")
                    or node.get("year")
                )

                rank = node.get("currentRank") or node.get("position")

                if title and isinstance(title, str) and (year or rating or rank):
                    try:
                        rank_int = int(rank) if rank else len(results) + 1
                    except (TypeError, ValueError):
                        rank_int = len(results) + 1

                    results.append({
                        "Rank": rank_int,
                        "Movie Title": title.strip(),
                        "Release Year": year,
                        "IMDb Rating": clean_rating(rating),
                    })

            for value in node.values():
                walk(value)

        elif isinstance(node, list):
            for value in node:
                walk(value)

    for script in soup.select('script[type="application/ld+json"], script#__NEXT_DATA__'):
        try:
            payload = json.loads(script.string or script.get_text())
            walk(payload)
        except (json.JSONDecodeError, TypeError, ValueError):
            continue

    unique = {}
    for movie in results:
        key = movie["Movie Title"].lower()
        if key not in unique:
            unique[key] = movie

    return sorted(unique.values(), key=lambda m: m["Rank"])


def get_chrome_driver():
    """Initializes and configures headless Chrome WebDriver with anti-detection options."""
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options

    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    )
    options.add_argument("--lang=en-US")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    options.add_experimental_option("prefs", {"intl.accept_languages": "en,en-US"})
    options.page_load_strategy = "eager"

    # Selenium 4.10+ has built-in Selenium Manager to locate / download chromedriver automatically
    driver = webdriver.Chrome(options=options)

    # Evade navigator.webdriver detection
    try:
        driver.execute_cdp_cmd(
            "Page.addScriptToEvaluateOnNewDocument",
            {"source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"},
        )
    except Exception as exc:
        logger.warning("Could not attach CDP anti-detection script: %s", exc)

    return driver


def scrape_with_selenium():
    """Scrape IMDb Top 250 using headless Chrome and BeautifulSoup."""
    driver = None
    try:
        logger.info("Initializing Selenium WebDriver in Headless Mode...")
        driver = get_chrome_driver()
        logger.info("Navigating to IMDb Top 250: %s", IMDB_URL)
        driver.get(IMDB_URL)

        # Allow initial hydration
        time.sleep(3)
        logger.info("IMDb page loaded: title='%s', source_length=%d", driver.title, len(driver.page_source))

        # Smooth scroll to ensure all 250 movies are loaded in DOM
        for _ in range(5):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1)

        html_content = driver.page_source
        soup = BeautifulSoup(html_content, "html.parser")

        movie_items = soup.select("li.ipc-metadata-list-summary-item")
        if not movie_items:
            movie_items = soup.select("ul.ipc-metadata-list > li")

        movies = []
        for index, item in enumerate(movie_items, start=1):
            try:
                movie = parse_movie_item(item, index)
                if movie:
                    movies.append(movie)
            except Exception as exc:
                logger.warning("Error parsing item %s: %s", index, exc)

        # If HTML list items didn't capture all 250, supplement with JSON data
        if len(movies) < 250:
            json_movies = extract_json_movies(soup)
            existing_keys = {(m["Movie Title"].lower(), m["Release Year"]) for m in movies}
            for jm in json_movies:
                key = (jm["Movie Title"].lower(), jm["Release Year"])
                if key not in existing_keys:
                    movies.append(jm)
                    existing_keys.add(key)

        logger.info("Selenium successfully parsed %s movies.", len(movies))
        return movies

    finally:
        if driver:
            try:
                driver.quit()
            except Exception:
                pass


def scrape_with_requests():
    """Fallback scraping using direct HTTP requests."""
    logger.info("Attempting HTTP requests fallback for IMDb...")
    response = requests.get(IMDB_URL, headers=HEADERS, timeout=15)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    movie_items = soup.select("li.ipc-metadata-list-summary-item") or soup.select("ul.ipc-metadata-list > li")

    movies = []
    for index, item in enumerate(movie_items, start=1):
        movie = parse_movie_item(item, index)
        if movie:
            movies.append(movie)

    if not movies:
        movies = extract_json_movies(soup)

    return movies


def load_cached_movies():
    """Load pre-cached IMDb Top 250 dataset as a dependable fallback."""
    if os.path.exists(FALLBACK_CSV_PATH):
        logger.info("Loading cached movie dataset from %s", FALLBACK_CSV_PATH)
        df = pd.read_csv(FALLBACK_CSV_PATH)
        records = df.to_dict(orient="records")
        for index, movie in enumerate(records, start=1):
            movie["Rank"] = int(movie.get("Rank") or index)
            movie["Movie Title"] = str(movie.get("Movie Title") or "").strip()
            movie["Release Year"] = clean_year(movie.get("Release Year"))
            movie["IMDb Rating"] = clean_rating(movie.get("IMDb Rating"))
        return records
    return []


def scrape_imdb_top_250():
    """
    Main scraper entrypoint.
    Executes real-time scraping via Selenium, falls back to requests,
    and falls back to cached dataset if access is restricted by anti-bot firewalls.
    """
    movies = []

    # 1. Primary: Selenium Headless Chrome
    try:
        movies = scrape_with_selenium()
    except Exception as exc:
        logger.warning("Selenium scraping failed: %s. Trying HTTP requests fallback...", exc)

    # 2. Secondary: Direct HTTP requests
    if not movies:
        try:
            movies = scrape_with_requests()
        except Exception as exc:
            logger.warning("HTTP requests scraping failed: %s.", exc)

    # 3. Tertiary: Cached dataset fallback
    if not movies:
        logger.warning("Live scraping blocked by anti-bot protection. Using cached IMDb Top 250 dataset.")
        movies = load_cached_movies()

    if not movies:
        raise RuntimeError("Failed to retrieve IMDb Top 250 movies from all available sources.")

    # Deduplicate by Title and Release Year, keeping valid ranks
    unique = {}
    for movie in movies:
        key = (movie["Movie Title"].strip().lower(), movie["Release Year"])
        if key not in unique:
            unique[key] = movie

    sorted_movies = sorted(unique.values(), key=lambda m: m["Rank"])[:250]

    # Ensure ranks 1..250 are continuous
    for index, movie in enumerate(sorted_movies, start=1):
        movie["Rank"] = index

    logger.info("Returning %s movies.", len(sorted_movies))
    return sorted_movies


if __name__ == "__main__":
    try:
        data = scrape_imdb_top_250()
        print(f"Total movies retrieved: {len(data)}")
        if data:
            print("First movie:", data[0])
            print("250th movie:", data[-1])
    except Exception as exc:
        print("Scraping error:", exc)
