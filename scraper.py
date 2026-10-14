
import json
import logging
import re

import requests
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

IMDB_URL = "https://www.imdb.com/chart/top/"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}


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
        value = value.get("aggregateRating")

    try:
        return float(value) if value is not None else 0.0
    except (TypeError, ValueError):
        return 0.0


def parse_movie_item(item, fallback_rank):
    """Extract a movie from an HTML list item."""
    title_element = item.select_one(
        "h3.ipc-title__text, h3, h4"
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

    return {
        "Rank": rank,
        "Movie Title": title,
        "Release Year": year,
        "IMDb Rating": rating,
    }


def extract_json_movies(soup):
    """Try extracting movie data from embedded JSON."""
    results = []

    def walk(node):
        if isinstance(node, dict):
            # IMDb JSON structures may use different field names.
            title_data = node.get("titleText")
            title = (
                title_data.get("text")
                if isinstance(title_data, dict)
                else None
            )

            if not title:
                title = node.get("name")

            rating_data = node.get("ratingsSummary") or {}
            rating = rating_data.get("aggregateRating", 0)

            year = clean_year(
                node.get("releaseYear")
                or node.get("datePublished")
                or node.get("year")
            )

            rank = node.get("currentRank") or node.get("position")

            if title and isinstance(title, str):
                # Ignore generic page titles and objects without
                # movie-specific data.
                if year or rating or rank:
                    try:
                        rank = int(rank) if rank else len(results) + 1
                    except (TypeError, ValueError):
                        rank = len(results) + 1

                    results.append({
                        "Rank": rank,
                        "Movie Title": title.strip(),
                        "Release Year": year,
                        "IMDb Rating": clean_rating(rating),
                    })

            for value in node.values():
                walk(value)

        elif isinstance(node, list):
            for value in node:
                walk(value)

    for script in soup.select(
        'script[type="application/ld+json"], script#__NEXT_DATA__'
    ):
        try:
            payload = json.loads(script.string or script.get_text())
            walk(payload)
        except (json.JSONDecodeError, TypeError, ValueError):
            continue

    # Remove duplicate titles.
    unique = {}

    for movie in results:
        key = movie["Movie Title"].lower()
        if key not in unique:
            unique[key] = movie

    return sorted(
        unique.values(),
        key=lambda movie: movie["Rank"],
    )


def scrape_imdb_top_250():
    """Scrape IMDb Top 250 movie information."""
    logger.info("Requesting IMDb Top 250 page...")

    try:
        response = requests.get(
            IMDB_URL,
            headers=HEADERS,
            timeout=25,
        )
        logger.info("IMDb HTTP status: %s", response.status_code)
        logger.info("IMDb response URL: %s", response.url)
        response.raise_for_status()

    except requests.RequestException as exc:
        logger.exception("IMDb request failed")
        raise RuntimeError(
            f"Could not access IMDb: {exc}"
        ) from exc

    soup = BeautifulSoup(response.text, "html.parser")

    page_title = (
        soup.title.get_text(" ", strip=True)
        if soup.title
        else "No page title"
    )

    logger.info("IMDb response title: %s", page_title)

    # Method 1: Parse the movie list from HTML.
    movie_items = soup.select(
        "li.ipc-metadata-list-summary-item"
    )

    if not movie_items:
        movie_items = soup.select(
            "ul.ipc-metadata-list > li"
        )

    movies = []

    for index, item in enumerate(movie_items, start=1):
        try:
            movie = parse_movie_item(item, index)
            if movie:
                movies.append(movie)
        except (ValueError, TypeError, AttributeError) as exc:
            logger.warning("Skipping item %s: %s", index, exc)

    # Method 2: Try embedded structured JSON.
    if not movies:
        logger.warning(
            "No HTML movie entries found; checking embedded JSON."
        )
        movies = extract_json_movies(soup)

    if not movies:
        logger.error(
            "No movie data found. Response preview: %s",
            response.text[:500],
        )
        raise RuntimeError(
            "IMDb returned no movie entries. "
            "It may be serving a blocked or changed page. "
            "Check Vercel Function Logs for the response title "
            "and preview."
        )

    # Remove duplicates and keep the first 250.
    unique = {}

    for movie in movies:
        key = movie["Movie Title"].strip().lower()
        if key and key not in unique:
            unique[key] = movie

    movies = sorted(
        unique.values(),
        key=lambda movie: movie["Rank"],
    )[:250]

    # Normalize ranks for entries without a valid rank.
    for index, movie in enumerate(movies, start=1):
        if not movie["Rank"]:
            movie["Rank"] = index

    logger.info("Extracted %s movies.", len(movies))
    return movies


if __name__ == "__main__":
    try:
        data = scrape_imdb_top_250()
        print("Movies extracted:", len(data))
        for movie in data[:5]:
            print(movie)
    except Exception as exc:
        logger.exception("Scraping failed")
        print("Scraping failed:", exc)
